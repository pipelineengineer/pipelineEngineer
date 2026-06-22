import pandas as pd
import operator

def layer_to_df(layer):
            cols = [f.name() for f in layer.fields()]
            data = ([f[col] for col in cols] for f in layer.getFeatures())
            df = pd.DataFrame.from_records(data=data, columns = cols)
            return df

def return_mto(project_data_df,assembly_field,assembly_list_df,filters_df,features):

    merged_df = project_data_df.merge(assembly_list_df,left_on=assembly_field,right_on='assembly')

    for feature in features:
        merged_df[f'{feature}_a'] = merged_df.apply(lambda row: row[f'{feature}_a'] if pd.notna(row[f'{feature}_a']) and isinstance(row[f'{feature}_a'], (int, float))else (row[row[f'{feature}_a']] if pd.notna(row[f'{feature}_a']) else None),axis=1)
        merged_df[f"{feature}_a"] = merged_df[f"{feature}_a"].clip(merged_df[f"{feature}_a_floor"],merged_df[f"{feature}_a_ceil"])

        merged_df[f'{feature}_b'] = merged_df.apply(lambda row: row[f'{feature}_b'] if pd.notna(row[f'{feature}_b']) and isinstance(row[f'{feature}_b'], (int, float))else (row[row[f'{feature}_b']] if pd.notna(row[f'{feature}_b']) else None),axis=1)
        merged_df[f"{feature}_b"] = merged_df[f"{feature}_b"].clip(merged_df[f"{feature}_b_floor"],merged_df[f"{feature}_b_ceil"])

        try:
            merged_df[f'{feature}_c'] = merged_df.apply(lambda row: row[f'{feature}_c'] if pd.notna(row[f'{feature}_c']) and isinstance(row[f'{feature}_c'], (int, float))else (row[row[f'{feature}_c']] if pd.notna(row[f'{feature}_c']) else None),axis=1)
            merged_df[f"{feature}_c"] = merged_df[f"{feature}_c"].clip(merged_df[f"{feature}_c_floor"],merged_df[f"{feature}_c_ceil"])
        except:
            pass
        
    merged_df = merged_df.drop(columns=[c for c in merged_df.columns if "floor" in c or "ceil" in c])

        
    ops = {
        "Equal": operator.eq,
        "Greater Than or Equal To": operator.ge,
        "Greater Than": operator.gt,
        "Less Than": operator.lt,
        "Less Than or Equal To": operator.le,
        "Not Equal": operator.ne,
    }

    merged_df["rule_met"] = False

    for _, rule in filters_df.iterrows():
        cond = (
            (merged_df["item"] == rule["item"])
            & ops[rule["operator"]](
                merged_df[rule["value_a"]],
                merged_df[rule["value_b"]]
            )
        )

        merged_df["rule_met"] |= cond

    merged_df = merged_df[~merged_df["rule_met"]]
    merged_df = merged_df.drop(columns='rule_met')
    merged_df = merged_df.reset_index(drop=True)

    return merged_df