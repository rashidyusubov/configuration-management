import os
import yaml
import zlib


def read_config(config_path):
    """
    Чтение конфигурационного файла YAML.
    """
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML configuration: {e}")


def read_git_object(repo_path, object_hash):
    """
    Чтение объекта Git из папки .git/objects.
    """
    object_path = os.path.join(repo_path, ".git", "objects", object_hash[:2], object_hash[2:])
    if not os.path.exists(object_path):
        raise FileNotFoundError(f"Git object not found: {object_path}")
    print(f"Reading object at: {object_path}")
    with open(object_path, 'rb') as file:
        content = file.read()
    return decompress_object(content)


def decompress_object(data):
    """
    Распаковка объекта Git.
    """
    try:
        decompressed_data = zlib.decompress(data).decode('utf-8')
        return decompressed_data
    except zlib.error as e:
        raise ValueError(f"Error decompressing git object: {e}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Error decoding git object content as UTF-8: {e}")


def parse_commit(commit_content):
    """
    Разбор содержимого коммита Git.
    """
    lines = commit_content.split('\n')
    parents = [line.split(' ')[1] for line in lines if line.startswith('parent')]
    message_index = lines.index('') + 1
    message = '\n'.join(lines[message_index:]).strip()
    return parents, message


def build_dependency_graph(repo_path, start_commit):
    """
    Построение графа зависимостей коммитов.
    """
    graph = []
    visited = set()

    def dfs(commit_hash):
        if commit_hash in visited:
            return
        visited.add(commit_hash)
        print(f"Processing commit: {commit_hash}")
        try:
            commit_content = read_git_object(repo_path, commit_hash)
        except Exception as e:
            print(f"Error reading commit {commit_hash}: {e}")
            return

        parents, message = parse_commit(commit_content)
        print(f"Commit {commit_hash} has parents: {parents}, message: '{message}'")
        for parent in parents:
            graph.append((commit_hash, parent, message))
            dfs(parent)

    dfs(start_commit)
    print("Final Graph:", graph)
    return graph


def generate_plantuml(graph, output_file):
    """
    Генерация кода PlantUML на основе графа зависимостей.
    """
    print(f"Generating PlantUML file: {output_file}")
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as file:
            file.write("@startuml\n")
            for child, parent, message in graph:
                file.write(f'"{child}\\n{message}" --> "{parent}\\n"\n')
            file.write("@enduml\n")
        print(f"Dependency graph saved in '{output_file}'")
    except FileNotFoundError:
        print(f"Error: File {output_file} not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")


def find_latest_commit(repo_path):
    """
    Нахождение хэша последнего коммита в ветке master.
    """
    head_path = os.path.join(repo_path, ".git", "refs", "heads", "master")
    if not os.path.exists(head_path):
        raise FileNotFoundError("Branch 'master' not found.")
    with open(head_path, 'r') as file:
        commit_hash = file.read().strip()
    print(f"Found latest commit hash: {commit_hash}")
    return commit_hash


if __name__ == "__main__":
    config_path = "../config/config.yaml"  # Путь к конфигурационному файлу

    try:
        config = read_config(config_path)
        visualization_tool_path = config['visualization_tool_path']
        repository_path = config['repository_path']
        output_file = config['output_file_path']

        # Нахождение хэша последнего коммита
        start_commit = find_latest_commit(repository_path)

        # Построение графа зависимостей
        dependency_graph = build_dependency_graph(repository_path, start_commit)

        # Генерация файла PlantUML
        generate_plantuml(dependency_graph, output_file)

    except Exception as e:
        print(f"Error: {e}")
