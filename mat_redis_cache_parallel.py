import time
import multiprocessing
import glob
import os
import redis

redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))
redis_client = redis.StrictRedis(host=redis_host, port=redis_port, db=0)

def read_matrix(line):
    size, data = line.strip().split(':')
    rows, cols = map(int, size.split('x'))
    matrix = [list(data[i:i+cols]) for i in range(0, len(data), cols)]
    return matrix

def count_isolated_ones(matrix):
    count = 0
    rows, cols = len(matrix), len(matrix[0])

    def is_isolated(i, j):
        for x in range(max(0, i - 1), min(rows, i + 2)):
            for y in range(max(0, j - 1), min(cols, j + 2)):
                if matrix[x][y] == '1' and (x != i or y != j):
                    return False
        return True

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == '1' and is_isolated(i, j):
                count += 1

    return count

def count_isolated_clusters_of_two_ones(matrix):
    count = 0
    rows, cols = len(matrix), len(matrix[0])
    visited = set()

    def is_isolated(i, j):
        count1 = 0
        for x in range(max(0, i - 1), min(rows, i + 2)):
            for y in range(max(0, j - 1), min(cols, j + 2)):
                if (x, y) not in visited and (x != i or y != j):
                    if matrix[x][y] == '1':
                        count1 += 1
        return count1 == 1

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == '1' and (i, j) not in visited:
                if is_isolated(i, j):
                    for x in range(max(0, i - 1), min(rows, i + 2)):
                        for y in range(max(0, j - 1), min(cols, j + 2)):
                            if matrix[x][y] == '1' and (x, y) not in visited and (x != i or y != j):
                                if is_isolated(x, y):
                                    count += 1
                                    visited.add((i, j))
                                    visited.add((x, y))
                                    break
    return count
def count_isolated_clusters_of_three_ones(matrix):
    count = 0
    rows, cols = len(matrix), len(matrix[0])
    visited = set()
    isolated_visited = set()

    def dfs(i, j, cluster):
        if i < 0 or i >= rows or j < 0 or j >= cols or matrix[i][j] != '1' or (i, j) in visited:
            return cluster
        visited.add((i, j))
        cluster.add((i, j))
        if len(cluster) > 3:
            return set()
        for x, y in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1),
                     (i - 1, j - 1), (i - 1, j + 1), (i + 1, j - 1), (i + 1, j + 1)]:
            cluster = dfs(x, y, cluster)
            if len(cluster) > 3:
                return set()
        return cluster

    def is_isolated(cluster):
        isolated_visited.clear()
        isolated_visited.update(cluster)
        for i, j in cluster:
            for x, y in [(i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1),
                         (i - 1, j - 1), (i - 1, j + 1), (i + 1, j - 1), (i + 1, j + 1)]:
                if 0 <= x < rows and 0 <= y < cols and matrix[x][y] == '1':
                    if (x, y) not in isolated_visited:
                        return False
        return True

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == '1' and (i, j) not in visited:
                cluster = dfs(i, j, set())
                if len(cluster) == 3 and is_isolated(cluster):
                    count += 1
    return count

def process_file(file_name):
    try:
        with open(file_name, 'r') as fin, open(file_name.replace('.in', '.out'), 'w') as fout:
            for line in fin:
                matrix = read_matrix(line)
                matrix_hash = hash(str(matrix))  
                cached_result = redis_client.get(str(matrix_hash))
                if cached_result:
                    isolated_ones, isolated_clusters_two, isolated_clusters_three = map(int, cached_result.decode('utf-8').split(','))
                else:
                    isolated_ones = count_isolated_ones(matrix)
                    isolated_clusters_two = count_isolated_clusters_of_two_ones(matrix)
                    isolated_clusters_three = count_isolated_clusters_of_three_ones(matrix)

                    redis_client.set(str(matrix_hash), f"{isolated_ones},{isolated_clusters_two},{isolated_clusters_three}", ex=3600)

                fout.write(f"{isolated_ones} {isolated_clusters_two} {isolated_clusters_three}\n")
    except Exception as e:
        print(f"Error processing file {file_name}: {e}")

def main():
    input_directory = "/mnt/input"
    input_files = glob.glob(os.path.join(input_directory, 'mat*.in'))

    with multiprocessing.Pool() as pool:
        pool.map(process_file, input_files)

if __name__ == '__main__':
    start_time = time.perf_counter()
    main()
    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")