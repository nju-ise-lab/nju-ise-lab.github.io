package main

import (
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"os"
	"strings"

	_ "modernc.org/sqlite"
)

const createPagesTableSQL = `
CREATE TABLE IF NOT EXISTS pages (
	path TEXT PRIMARY KEY,
	seed INTEGER NOT NULL DEFAULT 0,
	views INTEGER NOT NULL DEFAULT 0,
	updated_at TEXT NOT NULL
);`

type viewResponse struct {
	Path  string `json:"path"`
	Seed  int64  `json:"seed"`
	Views int64  `json:"views"`
	Total int64  `json:"total"`
}

type errorResponse struct {
	Error string `json:"error"`
}

type incrementRequest struct {
	Path string `json:"path"`
}

type seedEntry struct {
	Path      string `json:"path"`
	Seed      int64  `json:"seed"`
	ViewsSeed *int64 `json:"views_seed,omitempty"`
}

func openDatabase(path string) (*sql.DB, error) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, err
	}

	if _, err := db.Exec(createPagesTableSQL); err != nil {
		_ = db.Close()
		return nil, err
	}

	return db, nil
}

func importViewSeedFile(db *sql.DB, path string) error {
	path = strings.TrimSpace(path)
	if path == "" {
		return nil
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}

	var seeds []seedEntry
	if err := json.Unmarshal(data, &seeds); err != nil {
		return err
	}

	return importViewSeeds(db, seeds)
}

func importViewSeeds(db *sql.DB, seeds []seedEntry) error {
	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	for _, seed := range seeds {
		path, err := validatePath(seed.Path)
		if err != nil {
			return err
		}
		seedValue := seed.Seed
		if seedValue == 0 && seed.ViewsSeed != nil {
			seedValue = *seed.ViewsSeed
		}
		if seedValue < 0 {
			return errors.New("seed must be non-negative")
		}

		_, err = tx.Exec(`
INSERT INTO pages(path, seed, views, updated_at)
VALUES (?, ?, 0, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
ON CONFLICT(path) DO UPDATE SET
	seed = excluded.seed,
	updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now');`, path, seedValue)
		if err != nil {
			return err
		}
	}

	return tx.Commit()
}

func newHandler(db *sql.DB) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("/api/views", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			handleGetViews(w, r, db)
		case http.MethodPost:
			handlePostViews(w, r, db)
		default:
			writeJSON(w, http.StatusMethodNotAllowed, errorResponse{Error: "method not allowed"})
		}
	})
	return mux
}

func handleGetViews(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	path, err := validatePath(r.URL.Query().Get("path"))
	if err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: err.Error()})
		return
	}

	counts, err := getPageViews(db, path)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: "query views"})
		return
	}

	writeJSON(w, http.StatusOK, counts)
}

func handlePostViews(w http.ResponseWriter, r *http.Request, db *sql.DB) {
	defer r.Body.Close()

	var req incrementRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: "invalid JSON body"})
		return
	}

	path, err := validatePath(req.Path)
	if err != nil {
		writeJSON(w, http.StatusBadRequest, errorResponse{Error: err.Error()})
		return
	}

	counts, err := incrementPageViews(db, path)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, errorResponse{Error: "increment views"})
		return
	}

	writeJSON(w, http.StatusOK, counts)
}

func getPageViews(db *sql.DB, path string) (viewResponse, error) {
	resp := viewResponse{Path: path}
	err := db.QueryRow(`SELECT seed, views FROM pages WHERE path = ?`, path).Scan(&resp.Seed, &resp.Views)
	if errors.Is(err, sql.ErrNoRows) {
		return resp, nil
	}
	if err != nil {
		return viewResponse{}, err
	}

	resp.Total = resp.Seed + resp.Views
	return resp, nil
}

func incrementPageViews(db *sql.DB, path string) (viewResponse, error) {
	_, err := db.Exec(`
INSERT INTO pages(path, seed, views, updated_at)
VALUES (?, 0, 1, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
ON CONFLICT(path) DO UPDATE SET
	views = views + 1,
	updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now');`, path)
	if err != nil {
		return viewResponse{}, err
	}

	return getPageViews(db, path)
}

func validatePath(raw string) (string, error) {
	path := strings.TrimSpace(raw)
	if path == "" {
		return "", errors.New("path is required")
	}
	if !strings.HasPrefix(path, "/") {
		return "", errors.New("path must be site-relative")
	}
	if strings.HasPrefix(path, "//") || strings.Contains(path, "://") {
		return "", errors.New("external path is not allowed")
	}
	return path, nil
}

func writeJSON(w http.ResponseWriter, status int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(value)
}
