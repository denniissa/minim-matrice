import zipfile
import numpy as np
import pandas as pd
import time


def parse_instance_from_zip(file):
    lines = file.readlines()
    instance_name = ""
    d = 0
    r = 0
    SCj = []
    Dk = []
    Cjk = []

    i = 0  # Index pentru a itera prin lines
    while i < len(lines):
        line = lines[i].decode('utf-8').strip()
        if line.startswith("instance_name"):
            instance_name = line.split('=')[1].strip().strip('";')
        elif line.startswith("d ="):
            d = int(line.split('=')[1].strip().strip(';'))
        elif line.startswith("r ="):
            r = int(line.split('=')[1].strip().strip(';'))
        elif line.startswith("SCj ="):
            SCj = list(map(int, line.split('=')[1].strip().strip('[];').split()))
        elif line.startswith("Dk ="):
            Dk = list(map(int, line.split('=')[1].strip().strip('[];').split()))
        elif line.startswith("Cjk ="):
            # Extrage toate elementele Cjk, indiferent de linia în care apar
            costs = []
            while not line.endswith("];"):
                # Curățăm orice element care nu este un număr întreg
                costs.extend(
                    [x for x in line.replace('[', '').replace(']', '').replace(';', '').split() if x.isdigit()])
                i += 1
                line = lines[i].decode('utf-8').strip()
            # Curățăm și ultima linie de Cjk
            costs.extend([x for x in line.replace('[', '').replace(']', '').replace(';', '').split() if
                          x.isdigit()])

            # Creează matricea Cjk
            Cjk = np.array([list(map(int, costs[i:i + r])) for i in range(0, len(costs), r)])

            print(f"Dimensiunea lui Cjk citită: {Cjk.shape}")  # Debug: Verifică dimensiunea

            # Verificare dimensiune Cjk
            if Cjk.shape[0] != d or any(len(row) != r for row in Cjk):
                raise ValueError(
                    f"Dimensiunea lui Cjk este incorectă: {Cjk.shape} (trebuie să fie {d} x {r})")

        i += 1  # Crește indexul pentru a trece la următoarea linie

    return instance_name, d, r, SCj, Dk, Cjk


def min_cost_algorithm(SCj, Dk, Cjk):
    d = len(SCj)
    r = len(Dk)

    # Inițializăm soluția cu 0 (cantitățile transportate)
    transport = np.zeros((d, r))

    # Creăm o copie a cerințelor și capacităților pentru a le modifica pe parcurs
    remaining_capacity = np.array(SCj)
    remaining_demand = np.array(Dk)

    total_cost = 0
    num_iterations = 0

    # Costul foarte mare pentru a marca celulele "eliminate"
    INF_COST = 1e9

    while np.sum(remaining_capacity) > 0 and np.sum(remaining_demand) > 0:
        # Căutăm costul minim din matricea Cjk, ignorând valorile foarte mari (INF_COST)
        Cjk_copy = np.copy(Cjk)
        Cjk_copy[remaining_capacity == 0, :] = INF_COST  # Mark rows with 0 capacity
        Cjk_copy[:, remaining_demand == 0] = INF_COST  # Mark columns with 0 demand

        min_cost = np.min(Cjk_copy)
        min_index = np.unravel_index(np.argmin(Cjk_copy), Cjk_copy.shape)
        i, j = min_index

        # Determinăm cât putem transporta (minimul dintre capacitatea rămasă și cerința rămasă)
        quantity = min(remaining_capacity[i], remaining_demand[j])

        # Alocăm cantitatea în matricea de transport
        transport[i, j] = quantity

        # Actualizăm capacitățile și cerințele
        remaining_capacity[i] -= quantity
        remaining_demand[j] -= quantity

        # Adăugăm costul la total
        total_cost += quantity * Cjk[i, j]

        num_iterations += 1  # Incrementăm numărul de iterații

    # Verificăm dacă problema a fost soluționată cu succes
    is_solved = np.sum(remaining_capacity) == 0 and np.sum(remaining_demand) == 0

    return transport, total_cost, num_iterations, is_solved


def save_results(instances_results, output_file):
    df = pd.DataFrame(instances_results, columns=['Instance', 'Optimal Cost', 'Iterations', 'Run Time (s)', 'Solved'])
    df.to_excel(output_file, index=False)


def process_zip_file(zip_path, output_file):
    instances_results = []

    # Deschidem arhiva zip
    with zipfile.ZipFile(zip_path, 'r') as archive:
        for filename in archive.namelist():
            if filename.endswith('.dat'):
                with archive.open(filename) as file:
                    instance_name, d, r, SCj, Dk, Cjk = parse_instance_from_zip(file)

                    # Aplicăm algoritmul minim matrice
                    start_time = time.time()
                    transport, optimal_cost, num_iterations, is_solved = min_cost_algorithm(SCj, Dk, Cjk)
                    end_time = time.time()

                    # Calculăm timpul de rulare
                    run_time = end_time - start_time

                    # Adăugăm rezultatul la listă
                    instances_results.append([instance_name, optimal_cost, num_iterations, run_time, is_solved])

    save_results(instances_results, output_file)


zip_path = r'C:\Users\deniv\PycharmProjects\probleme_transport\FCR_instances.zip'
output_file = r'C:\Users\deniv\PycharmProjects\probleme_transport\FCR_results.xlsx'  # Path pentru salvarea rezultatelor
process_zip_file(zip_path, output_file)