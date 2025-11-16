import os
from pathlib import Path

# --- Configuration ---
# Directories to completely ignore
IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", ".venv",
    ".idea", ".vscode", "build", "dist", "docs",
    ".parcel-cache", ".cache", ".next", ".husky", ".pnpm-store",
    "coverage", "tmp", "temp", ".terraform"
}

# File extensions to ignore (binary/large or non-source)
IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".ico",
    ".svg", ".webp", ".avif",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf",
    ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".db", ".sqlite", ".sqlite3",
    ".lock", ".log",
    ".parquet", ".h5", ".hdf5", ".pt", ".onnx", ".tif", ".tiff",
    ".shp", ".dbf", ".nc"
}

# Individual files to ignore (by name)
IGNORED_FILENAMES = {
    "yarn.lock", "pnpm-lock.yaml", "package-lock.json",
    ".DS_Store", ".env", ".env.local", ".env.production", ".env.development",
    ".python-version", ".tool-versions",
}

# Max file size to read (in bytes). Skip anything larger.
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024  # 2 MB

# Prefer to read only these code-like extensions unless a file looks like a schema
ALLOWED_CODE_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".kt", ".go",
    ".rs", ".rb", ".php", ".c", ".cc", ".cpp", ".h", ".hpp",
    ".cs", ".sql", ".yml", ".yaml", ".toml", ".ini", ".cfg",
    ".prisma", ".graphql", ".gql", ".md"  # md is helpful for schema notes
}

# Heuristics: paths that often contain DB schema or migrations
SCHEMA_HINT_DIRS = {
    "prisma", "migrations", "migration", "db", "database",
    "sql", "schema", "alembic", "migrate", "migrations_sql", "liquibase", "flyway"
}

# Heuristics: filenames/patterns that look like schema/migration definitions
SCHEMA_HINT_NAMES = {
    "schema.prisma", "schema.sql", "init.sql", "migration.sql",
    "migration", "migrations", "entities", "models", "alembic.ini",
    "seeder", "seed.sql", "DDL.sql"
}

def looks_like_schema_file(path: Path) -> bool:
    """Detect files that likely contain DB schema or table definitions."""
    name = path.name.lower()
    parts = {p.lower() for p in path.parts}

    # Strong hints: directories that typically hold schema/migrations
    if parts & SCHEMA_HINT_DIRS:
        return True

    # Filenames that scream 'schema/migration'
    for key in SCHEMA_HINT_NAMES:
        if key in name:
            return True

    # SQL files are often schema; keep them
    if path.suffix.lower() == ".sql":
        return True

    # Prisma schema
    if path.suffix.lower() == ".prisma":
        return True

    # ORM entity/model files are valuable
    if any(seg in parts for seg in {"entities", "entity", "models", "model"}):
        return path.suffix.lower() in {".ts", ".js", ".tsx", ".jsx", ".py", ".rb", ".java", ".kt"}

    return False

def is_large(path: Path) -> bool:
    try:
        return path.stat().st_size > MAX_FILE_SIZE_BYTES
    except Exception:
        # If we can't stat, treat it as not large so the normal ignore rules apply
        return False

def is_ignored(path: Path, output_filename: str) -> bool:
    """Check if a file or directory should be ignored."""
    # Ignore the output file itself
    if path.name == output_filename:
        return True

    # Ignore specific filenames
    if path.name in IGNORED_FILENAMES:
        return True

    # Ignore directories by any segment
    if any(part in IGNORED_DIRS for part in path.parts):
        return True

    # Skip large files
    if path.is_file() and is_large(path):
        return True

    # Ignore obvious data files (csv/json/jsonl/ndjson/geojson) unless they are tiny and inside schema dirs
    if path.suffix.lower() in {".csv", ".json", ".jsonl", ".ndjson", ".geojson"}:
        # allow only if it looks like schema/meta and small
        if not looks_like_schema_file(path) or is_large(path):
            return True

    # Ignore by extension if it's not code-like AND not a schema-like file
    if path.is_file():
        if looks_like_schema_file(path):
            return False  # keep schema-like files regardless of extension limits
        # Otherwise keep only code-like files
        if path.suffix.lower() not in ALLOWED_CODE_EXTENSIONS:
            return True

    # Finally, block anything with explicitly ignored extensions
    if path.suffix.lower() in IGNORED_EXTENSIONS:
        return True

    return False

def generate_tree(root_path: Path, output_filename: str):
    """Generates the directory tree structure and returns a list of files to process."""
    tree_lines = []
    files_to_dump = []
    schema_files = []

    for root, dirs, files in os.walk(root_path, topdown=True):
        # Filter out ignored directories
        dirs[:] = [d for d in dirs if not is_ignored(Path(root) / d, output_filename)]

        level = root.replace(str(root_path), '').count(os.sep)
        indent = ' ' * 4 * level

        # Add the current directory to the tree
        if level > 0 or root == str(root_path):
            dir_name = os.path.basename(root)
            if dir_name:
                tree_lines.append(f'{indent}📂 {dir_name}/')

        sub_indent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            file_path = Path(root) / f
            if not is_ignored(file_path, output_filename):
                mark = "📄"
                if looks_like_schema_file(file_path):
                    mark = "🗄️"  # mark likely schema files
                    schema_files.append(file_path)
                tree_lines.append(f'{sub_indent}{mark} {f}')
                files_to_dump.append(file_path)

    return "\n".join(tree_lines), files_to_dump, schema_files

def main():
    """Main function to run the project dumper."""
    while True:
        project_dir_input = input("Please enter the path to the project directory (e.g., '.' for current): ")
        project_path = Path(project_dir_input)
        if project_path.is_dir():
            break
        else:
            print(f"❌ Error: The path '{project_dir_input}' is not a valid directory. Please try again.")

    output_filename_input = input("Enter the output file name (default: project_dump.txt): ")
    output_filename = output_filename_input if output_filename_input else "project_dump.txt"

    print(f"\n🚀 Starting to process project directory: {project_path.resolve()}")
    print(f"Ignoring directories: {', '.join(sorted(IGNORED_DIRS))}")
    print(f"Ignoring extensions: {', '.join(sorted(IGNORED_EXTENSIONS))}")
    print(f"Max file size: {MAX_FILE_SIZE_BYTES} bytes\n")

    try:
        tree_structure, files_to_dump, schema_files = generate_tree(project_path, output_filename)
        output_path = project_path / output_filename

        with open(output_path, "w", encoding="utf-8", errors="ignore") as f:
            f.write(f"Project: {project_path.resolve().name}\n\n")
            f.write("--- REPO TREE STRUCTURE ---\n\n")
            f.write(tree_structure)
            f.write("\n\n" + "="*80 + "\n\n")

            # Highlight schema files up front
            f.write("--- LIKELY DB SCHEMA / MIGRATION FILES ---\n\n")
            if schema_files:
                for p in schema_files:
                    f.write(f"- {p.relative_to(project_path)}\n")
            else:
                f.write("(none detected)\n")
            f.write("\n" + "="*80 + "\n\n")

            f.write("--- FILE CONTENTS ---\n\n")
            for file_path in files_to_dump:
                relative_path = file_path.relative_to(project_path)
                f.write("="*20 + f" FILE: {relative_path} " + "="*20 + "\n\n")
                try:
                    # Read text; binary-ish files will be skipped earlier
                    content = file_path.read_text(encoding="utf-8")
                    f.write(content)
                    f.write("\n\n")
                except Exception as e:
                    f.write(f"[Could not read file: {e}]\n\n")

        print(f"\n✅ Success! Project dump created at: {output_path.resolve()}")
        print(f"Total files processed: {len(files_to_dump)}")
        if schema_files:
            print("🗄️ Detected potential schema/migration files:")
            for p in schema_files:
                print("  -", p.relative_to(project_path))
        else:
            print("ℹ️ No obvious schema/migration files detected.")

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
