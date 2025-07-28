from services.indexing_service import IndexingService

def test_indexing():
    indexer = IndexingService()
    print("🔄 Starting indexing...")
    indexer.index_files()

    print("🔍 Loading indexed data...")
    indexed = indexer.load_index()
    print(f"✅ Total indexed files: {len(indexed)}")

    if indexed:
        print("\n📂 Sample indexed files:")
        for i, entry in enumerate(indexed[:5]):
            if isinstance(entry, tuple):
                path, content = entry
            else:
                path, content = entry, ""
            print(f"  {i+1}. {path}")
            if content:
                print(f"     → Preview: {content[:100]!r}")
    else:
        print("⚠️ Index is empty. Check search paths or file formats.")

if __name__ == "__main__":
    test_indexing()
