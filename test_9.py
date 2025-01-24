a = [[1, 3, 4], [1], [7, 8]]
b = [item for sublist in a for item in sublist]
print(b)