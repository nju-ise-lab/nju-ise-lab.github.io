package main

import (
	"log"
	"net/http"
	"os"
)

func main() {
	dbPath := os.Getenv("VIEW_COUNTER_DB")
	if dbPath == "" {
		dbPath = "views.db"
	}

	addr := os.Getenv("ADDR")
	if addr == "" {
		addr = ":8080"
	}

	db, err := openDatabase(dbPath)
	if err != nil {
		log.Fatalf("open database: %v", err)
	}
	defer db.Close()

	seedFile := os.Getenv("VIEW_COUNTER_SEED_FILE")
	if err := importViewSeedFile(db, seedFile); err != nil {
		log.Fatalf("import view seed file: %v", err)
	}

	log.Printf("view counter listening on %s, db=%s", addr, dbPath)
	if err := http.ListenAndServe(addr, newHandler(db)); err != nil {
		log.Fatalf("listen and serve: %v", err)
	}
}
