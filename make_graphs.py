import os
import pandas as pd
import numpy as np
from collections import defaultdict
import ast
from datetime import datetime
import networkx as nx
import pickle
import argparse
import sys


parser = argparse.ArgumentParser(
    prog='make_graphs.py',
    description='Takes as input a setmorph processed lexicon and a paralex sound file, and outputs a bipartite graph of exponent triphones and/or a one-mode graph of the lexemes',
    epilog='combine_exponents.py setmorph_lexicon')

parser.add_argument('-f', '--filepath', required=True, help='Path to the input CSV file')

# Optional argument for graph type
parser.add_argument('-g', '--graphs',
                    choices=['all', 'onemode', 'bipartite'],
                    default='all',
                    help='Type of graph to generate (default: all)')

args = parser.parse_args()


def find_consecutive_sets(lst):
    # Sort the list to ensure the numbers are in ascending order
    lst.sort()

    # Initialize an empty list to store the consecutive sets
    consecutive_sets = []

    # Initialize an empty list to store the current set of consecutive numbers
    current_set = []

    for number in lst:
        if not current_set:
            # If current_set is empty, start a new set with the current number
            current_set.append(number)
        else:
            if number == current_set[-1] + 1:
                # If the current number is consecutive, add it to the current set
                current_set.append(number)
            else:
                # If the current number is not consecutive, store the current set and start a new one
                consecutive_sets.append(current_set)
                current_set = [number]

    # Add the last set if it has elements
    if current_set:
        consecutive_sets.append(current_set)

    return consecutive_sets



filepath = args.filepath
folder, filename = os.path.split(os.path.abspath(filepath))
filecode = filename.removesuffix("_exponents.csv_formatives")

with open(filepath) as f:
    df = pd.read_csv(f)

# add in zero exponents
a = df.groupby("lexeme")["dist"].apply(list)
a = a.apply(lambda x: list(set([c for l in x for c in l.split(" ")])))

zero_list = []
for lex in df["lexeme"].unique():
    cells_in_df = df[(df["lexeme"] == lex) & (~df["exponence"].isna())]["dist"].values
    cells_in_df = list(set([x for dist in cells_in_df for x in dist.split(" ")]))
    diff = list(set(a[lex]) - set(cells_in_df))
    if diff:
        for cell in diff:
            zero_list.append([lex, 1, "segmental", "", cell])

df["dist"] = df["dist"].str.split(" ")
df["dist"] = np.where(df["exponence"].isna(), "stem", df["dist"])
df = df[["lexeme", "slot", "tier", "formative", "dist"]]
df = df.explode("dist")
df = pd.concat([df, pd.DataFrame(zero_list, columns=["lexeme", "slot", "tier", "formative", "dist"])])

# combine exponents in successive positions based on columns
result = defaultdict()

for lexeme, group in df.groupby('lexeme'):
    result[lexeme] = defaultdict()
    # Process each cell (distribution) within the lexeme
    for cell, sub_group in group.groupby('dist'):
        for tier, sub_sub_group in sub_group.groupby("tier"):
            if len(sub_sub_group) == 1:
                if cell not in result[lexeme]:
                    result[lexeme][cell] = [sub_sub_group["formative"].values[0]]
                else:
                    result[lexeme][cell].append(sub_sub_group["formative"].to_list())
            else:
                slots = sub_sub_group["slot"].values
                cons_slots = find_consecutive_sets(slots)
                for slots in cons_slots:
                    combined_formative = "".join(sub_sub_group[sub_sub_group["slot"].isin(slots)]["formative"].values)
                    if cell not in result[lexeme]:
                        result[lexeme][cell] = [combined_formative]
                    else:
                        result[lexeme][cell].append(combined_formative)

formatives = pd.DataFrame.from_dict(result, orient="index")


def flatten_lists_in_dataframe(df):
    def flatten(item):
        if isinstance(item, (list, np.ndarray, pd.Series)):
            return [subitem for i in item for subitem in flatten(i)]
        return [item]

    def process_cell(cell):
        if isinstance(cell, (list, np.ndarray, pd.Series)):
            return flatten(cell)
        return [cell]  # Always return a list, even for single items

    def safe_process(x):
        try:
            return process_cell(x) if pd.notna(x).all() else [x]
        except AttributeError:
            return process_cell(x) if pd.notna(x) else [x]

    return df.map(safe_process)


formatives = flatten_lists_in_dataframe(formatives)
# step 2 - for any exponent sets that have more than one item, check if the combination of those items is an exponent in
# that cell elsewhere in the system. If yes, combine the exponents

# dictionary with all exponents in a given cell
# exponent_set = defaultdict()
# for x in [key for key in formatives.columns if key != "stem"]:
#     exponent_set[x] = list(set([exp for lst in formatives[x].values.tolist() if str(lst) != "nan" for exp in lst]))
#
# formatives_dict = formatives.to_dict(orient="index")
#
# def combine_exponents(exp_list, exps_cell):
#     final_exp_list = []
#     i = 0
#
#     while i < len(exp_list):
#         combined_found = False
#         for end in range(len(exp_list), i, -1):
#             combined_exps = "".join(exp_list[i:end])
#             if combined_exps in exps_cell:
#                 final_exp_list.append(combined_exps)
#                 del exp_list[i:end]
#                 combined_found = True
#                 break  # Exit the inner loop to restart from the new i
#         if not combined_found:
#             i += 1  # Only move forward if no combination was found
#
#     return final_exp_list

# new_dict = defaultdict()
# for lex, cell_dict in formatives_dict.items():
#     new_dict[lex] = defaultdict()
#     for cell, exps in cell_dict.items():
#         if cell != "stem" and str(exps) != "nan":
#             new_dict[lex][cell] = combine_exponents(cell_dict[cell], exponent_set[cell])

#df_combo = pd.DataFrame.from_dict(new_dict, orient="index")


# cell_values = {'GEN.N.SG': "GEN.SG", 'N.SG.DAT': "DAT.SG", 'INS.N.SG': "INS.SG", 'VOC.N.SG': "VOC.SG", 'stem': "STEM", 'ACC.PL.N': "ACC.PL", 'ACC.N.SG': "ACC.SG", 'GEN.PL.N': "GEN.PL", 'PL.N.DAT':"DAT.PL", 'INS.PL.N':"INS.PL", 'VOC.PL.N':"VOC.PL", 'PL.N.NOM':"NOM.PL", 'N.SG.NOM':"NOM.SG"}
# df_combo = df_combo.rename(columns = cell_values)

# df_combo = df_combo[["STEM", "NOM.SG", "GEN.SG", "DAT.SG", "ACC.SG", "VOC.SG", "INS.SG", "NOM.PL", "GEN.PL", "DAT.PL", "ACC.PL", "VOC.PL", "INS.PL" ]]
formatives.to_csv(folder + "/formatives_combined.csv")
df_combo = formatives
df_combo = df_combo.drop(columns="stem")


def process_cell(cell, column_name):
    if isinstance(cell, list):
        exponent_list = [f"{exponent}-{column_name}" for exponent in cell]
        return exponent_list
    return []


# Apply the function to each cell in the DataFrame
lexeme_dict = defaultdict(list)
for idx, row in df_combo.iterrows():
    triphone_list = []
    for col in df_combo.columns:
        cell = row[col]
        tagged_exps = process_cell(cell, col)
        lexeme_dict[idx] += (tagged_exps)

indexed_dict = {}
for idx, exps_list in lexeme_dict.items():
    seen = defaultdict(int)
    indexed_exps = []
    for exp in exps_list:
        seen[exp] += 1
        if seen[exp] > 1:
            indexed_exps.append(f"{exp}_{seen[exp] - 1}")
        else:
            indexed_exps.append(exp)
    indexed_dict[idx] = indexed_exps

#make graphs

print(datetime.now().strftime('%H:%M:%S')+" Prepping df")

def dict_to_tuple_list(input_dict):
    result = []
    for key, value_list in input_dict.items():
        result.extend([key, value] for value in value_list)
    return result


formatives = formatives.rename_axis("lexeme").reset_index()

df_weights = pd.melt(formatives, id_vars = "lexeme").reset_index()
df_weights["length"] = df_weights.apply(lambda x: len(x["value"]), axis = 1)
df_weights = df_weights[["lexeme", "variable", "length"]]
df_weights = pd.pivot_table(df_weights, values="length", index="lexeme", columns="variable")
weights_dict = df_weights.to_dict(orient = "index")

edges = dict_to_tuple_list(indexed_dict)
for lst in edges:
    cell = lst[1].split("-")[1]
    if "_" in cell:
        cell = cell.split("_")[0]
    lst.append(1/weights_dict[lst[0]][cell])

lexemes = list(indexed_dict.keys())
exponent = list(set([x for lst in indexed_dict.values() for x in lst]))


print(datetime.now().strftime('%H:%M:%S')+" making bipartite")
B = nx.Graph()
B.add_nodes_from(lexemes, bipartite=0)
B.add_nodes_from(exponent, bipartite=1)
for lst in edges:
    B.add_edge(lst[0], lst[1], weight = lst[2])

#bipartite needs to have weighed edges based on how many exponents per cell per lexeme there are
print(datetime.now().strftime('%H:%M:%S')+" picking bipartite")
with open(folder+"/"+filecode+"_bipartite.pickle", 'wb') as handle:
    pickle.dump(B, handle, protocol=pickle.HIGHEST_PROTOCOL)


print(datetime.now().strftime('%H:%M:%S')+" projecting one mode")
G = nx.algorithms.bipartite.weighted_projected_graph(B, lexemes)

print(datetime.now().strftime('%H:%M:%S')+" pickling one mode")
with open(folder+"/"+filecode+"_onemodeweighed.pickle", 'wb') as handle:
    pickle.dump(G, handle, protocol=pickle.HIGHEST_PROTOCOL)
print(datetime.now().strftime('%H:%M:%S')+" done")


