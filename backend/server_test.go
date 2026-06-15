package main

import (
	"bytes"
	"database/sql"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"
)

func setupTestHandler(t *testing.T) (*sql.DB, http.Handler) {
	t.Helper()

	db, err := openDatabase(filepath.Join(t.TempDir(), "views.db"))
	if err != nil {
		t.Fatalf("open database: %v", err)
	}
	t.Cleanup(func() {
		_ = db.Close()
	})

	return db, newHandler(db)
}

func decodeJSON(t *testing.T, rec *httptest.ResponseRecorder) map[string]any {
	t.Helper()

	var got map[string]any
	if err := json.Unmarshal(rec.Body.Bytes(), &got); err != nil {
		t.Fatalf("decode response JSON: %v; body=%q", err, rec.Body.String())
	}
	return got
}

func writeSeedFile(t *testing.T, body string) string {
	t.Helper()

	path := filepath.Join(t.TempDir(), "views-seed.json")
	if err := os.WriteFile(path, []byte(body), 0644); err != nil {
		t.Fatalf("write seed file: %v", err)
	}
	return path
}

func TestGetMissingPathReturnsZeroCounts(t *testing.T) {
	_, handler := setupTestHandler(t)

	req := httptest.NewRequest(http.MethodGet, "/api/views?path=/news/a/", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["path"] != "/news/a/" || got["seed"] != float64(0) || got["views"] != float64(0) || got["total"] != float64(0) {
		t.Fatalf("response = %#v, want zero counts for /news/a/", got)
	}
}

func TestPostIncrementsViews(t *testing.T) {
	_, handler := setupTestHandler(t)

	body := bytes.NewBufferString(`{"path":"/news/a/"}`)
	req := httptest.NewRequest(http.MethodPost, "/api/views", body)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["path"] != "/news/a/" || got["views"] != float64(1) || got["total"] != float64(1) {
		t.Fatalf("response = %#v, want views and total incremented to 1", got)
	}
}

func TestRejectsEmptyPath(t *testing.T) {
	_, handler := setupTestHandler(t)

	body := bytes.NewBufferString(`{"path":""}`)
	req := httptest.NewRequest(http.MethodPost, "/api/views", body)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusBadRequest, rec.Body.String())
	}
}

func TestRejectsExternalPath(t *testing.T) {
	_, handler := setupTestHandler(t)

	body := bytes.NewBufferString(`{"path":"https://example.com/news/a/"}`)
	req := httptest.NewRequest(http.MethodPost, "/api/views", body)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusBadRequest {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusBadRequest, rec.Body.String())
	}
}

func TestSeedAndViewsTotalCalculation(t *testing.T) {
	db, handler := setupTestHandler(t)

	_, err := db.Exec(
		`INSERT INTO pages(path, seed, views, updated_at) VALUES (?, ?, ?, current_timestamp)`,
		"/news/seeded/",
		42,
		3,
	)
	if err != nil {
		t.Fatalf("insert seeded page: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/api/views?path=/news/seeded/", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["seed"] != float64(42) || got["views"] != float64(3) || got["total"] != float64(45) {
		t.Fatalf("response = %#v, want seed 42 + views 3 = total 45", got)
	}
}

func TestImportViewSeedFileAddsSeedToTotal(t *testing.T) {
	db, handler := setupTestHandler(t)

	seedFile := writeSeedFile(t, `[{"path":"/news/a/","seed":42}]`)
	if err := importViewSeedFile(db, seedFile); err != nil {
		t.Fatalf("import seed file: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/api/views?path=/news/a/", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["seed"] != float64(42) || got["views"] != float64(0) || got["total"] != float64(42) {
		t.Fatalf("response = %#v, want seed 42 + views 0 = total 42", got)
	}
}

func TestImportViewSeedFileAcceptsLegacyViewsSeedField(t *testing.T) {
	db, handler := setupTestHandler(t)

	seedFile := writeSeedFile(t, `[{"path":"/news/a/","views_seed":42}]`)
	if err := importViewSeedFile(db, seedFile); err != nil {
		t.Fatalf("import seed file: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/api/views?path=/news/a/", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["seed"] != float64(42) || got["views"] != float64(0) || got["total"] != float64(42) {
		t.Fatalf("response = %#v, want legacy views_seed 42 to import as seed", got)
	}
}

func TestImportViewSeedFilePreservesExistingViews(t *testing.T) {
	db, handler := setupTestHandler(t)

	for i := 0; i < 2; i++ {
		body := bytes.NewBufferString(`{"path":"/news/a/"}`)
		req := httptest.NewRequest(http.MethodPost, "/api/views", body)
		rec := httptest.NewRecorder()

		handler.ServeHTTP(rec, req)

		if rec.Code != http.StatusOK {
			t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
		}
	}

	seedFile := writeSeedFile(t, `[{"path":"/news/a/","seed":42}]`)
	if err := importViewSeedFile(db, seedFile); err != nil {
		t.Fatalf("import seed file: %v", err)
	}
	if err := importViewSeedFile(db, seedFile); err != nil {
		t.Fatalf("import seed file again: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/api/views?path=/news/a/", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["seed"] != float64(42) || got["views"] != float64(2) || got["total"] != float64(44) {
		t.Fatalf("response = %#v, want repeated import to keep views 2 and total 44", got)
	}
}

func TestImportViewSeedFileEmptyPathIsNoop(t *testing.T) {
	db, handler := setupTestHandler(t)

	if err := importViewSeedFile(db, ""); err != nil {
		t.Fatalf("import empty seed file path: %v", err)
	}

	req := httptest.NewRequest(http.MethodGet, "/api/views?path=/news/a/", nil)
	rec := httptest.NewRecorder()

	handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d; body=%q", rec.Code, http.StatusOK, rec.Body.String())
	}
	got := decodeJSON(t, rec)
	if got["seed"] != float64(0) || got["views"] != float64(0) || got["total"] != float64(0) {
		t.Fatalf("response = %#v, want no seed file path to leave counts at 0", got)
	}
}
