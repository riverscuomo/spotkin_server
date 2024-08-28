import os
import fnmatch
import markdown


def load_gitignore_patterns(gitignore_path):
    """Load .gitignore patterns into a list."""
    patterns = []
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                # Remove comments and empty lines
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith('#'):
                    patterns.append(stripped_line)
    return patterns


def should_ignore(file_path, ignore_patterns):
    """Check if a file should be ignored based on .gitignore patterns."""
    for pattern in ignore_patterns:
        if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
            return True
    return False


def is_binary_file(file_path):
    """Check if a file is binary by reading a portion of it."""
    try:
        with open(file_path, 'rb') as file:
            chunk = file.read(1024)
            if b'\0' in chunk:  # NULL byte indicates binary file
                return True
    except:
        pass
    return False


def traverse_project(directory, ignore_patterns):
    """Traverse the project directory and collect file paths."""
    files_to_include = []
    for root, dirs, files in os.walk(directory):
        # Check if any directories should be skipped
        dirs[:] = [d for d in dirs if not should_ignore(
            os.path.join(root, d), ignore_patterns)]
        for file in files:
            file_path = os.path.join(root, file)
            if not should_ignore(file_path, ignore_patterns) and not is_binary_file(file_path):
                print(file_path)
                files_to_include.append(file_path)
    return files_to_include


def write_to_markdown(files, output_file):
    """Write the content of files to a Markdown file."""
    with open(output_file, 'w', encoding='utf-8') as md_file:
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    md_file.write(f"## {file_path}\n\n")
                    md_file.write(
                        "```" + os.path.splitext(file_path)[1].lstrip('.') + "\n")
                    md_file.write(file.read())
                    md_file.write("\n```\n\n")
            except UnicodeDecodeError:
                print(f"Skipping {file_path} due to encoding issues.")
            except Exception as e:
                print(f"An error occurred while processing {file_path}: {e}")


def main():
    project_directory = '.'  # Current directory, change if needed
    gitignore_path = os.path.join(
        project_directory, '.gitignore', )
    output_file = 'dump.md'

    ignore_patterns = load_gitignore_patterns(gitignore_path)
    ignore_patterns.extend(
        ['.gitignore', output_file, '.\spotkin\data', 'CHANGELOG.md',  'LICENSE', '.git', 'spotkin.egg-info', '.\code-based.md', '.\dump.py', '.\.vscode', '.\spotkin\copy_sheet.py'])
    files_to_include = traverse_project(project_directory, ignore_patterns)

    write_to_markdown(files_to_include, output_file)
    print(
        f"Markdown file '{output_file}' has been created with the project content.")


if __name__ == "__main__":
    main()
