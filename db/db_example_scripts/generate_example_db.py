import sqlite3

resistors = [
    {"TOL": [20], "VAL": [10, 15, 22, 33, 47, 68]},
    {"TOL": [10], "VAL": [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]},
    {"TOL": [5, 1], "VAL": [10, 11, 12, 13, 15, 16, 18, 20, 22, 24,
                            27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91]},
    {"TOL": [2], "VAL": [100, 105, 110, 115, 121, 127, 133, 140, 147, 154, 162, 169, 178, 187, 196, 205, 215,
                         226, 237, 249, 261, 274, 287, 301, 316, 332, 348, 365, 383, 402, 422, 442, 464, 487,
                         511, 536, 562, 590, 619, 649, 681, 715, 750, 787, 825, 866, 909, 953]},
    {"TOL": [1], "VAL": [100, 102, 105, 107, 110, 113, 115, 118, 121, 124, 127, 130, 133, 137, 140, 143, 147, 150, 154, 158, 162,
                         165, 169, 174, 178, 182, 187, 191, 196, 200, 205, 210, 215, 221, 226, 232, 237, 243, 249, 255, 261, 267,
                         274, 280, 287, 294, 301, 309, 316, 324, 332, 340, 348, 357, 365, 374, 383, 392, 402, 412, 422, 432, 442,
                         453, 464, 475, 487, 499, 511, 523, 536, 549, 562, 576, 590, 604, 619, 634, 649, 665, 681, 698, 715, 732,
                         750, 768, 787, 806, 825, 845, 866, 887, 909, 931, 953, 976]},
]

exp = [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000, 100000, 1000000, 10000000]
powers = [0.125, 0.25, 0.5, 1, 2, 3, 4, 5]
types = [2, 3, 6, 8]

connection = sqlite3.connect(
    "./db/database.sqlite")
cursor = connection.cursor()

for series in resistors:
    tolerances = series["TOL"]
    values = series["VAL"]

    for res_type in types:
        for tolerance in tolerances:
            for power in powers:
                for exponent in exp:
                    for value in values:
                        # print(
                        #     f"Value: {value*exponent} Tolerance: {tolerance} Power: {power} Type_ID: 2")
                        db_value = value * exponent
                        cursor.execute(
                            "INSERT INTO Resistors (Value, Tolerance, Power, Type_ID) VALUES (?, ?, ?, ?)",
                            (db_value, tolerance, power, res_type)
                        )

connection.commit()
connection.close()
