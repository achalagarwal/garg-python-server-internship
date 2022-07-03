import re
from typing import List, Tuple

EXTRACT_NUMBERS_REGEX = re.compile(r"((?:[0-9]*[.])?(?:[0-9]+))")


def parse_raw_invoice_dataframe(dataframe) -> List[Tuple[str, float, str]]:
    searchfor = ["Quantity", "Qty", "Amount", "Rate", "Description", "Tax", "Total"]

    title_row = None
    title_row_index = None
    max_count = 0

    for i, row in dataframe.iterrows():
        contains = row.str.contains("|".join(searchfor), case=False)
        count = contains.sum()
        if count > max_count:
            title_row = row
            title_row_index = i
            max_count = count

    # sometimes the index can be garbage string because of invoice structure or pdf parsing errors
    title_row.reset_index(drop=True, inplace=True)

    # get title row
    description_searchfor = ["name", "description", "title"]
    description_rows_series = title_row.str.contains(
        "|".join(description_searchfor), case=False, na=False
    )
    description_rows = description_rows_series[description_rows_series].index.values

    # get quantity row
    quantity_searchfor = ["Quantity", "Units", "Qty"]
    quantity_rows_series = title_row.str.contains(
        "|".join(quantity_searchfor), case=False, na=False
    )
    quantity_rows = quantity_rows_series[quantity_rows_series].index.values

    # iterate through the rows after the title row
    # to find the rows with data
    # each row can have multiple data entries
    descriptions = []

    desc_quantity_dict = {}

    for i, row in dataframe.iloc[title_row_index + 1 :].iterrows():
        # extract data from description rows
        # to check if there is data
        # import pdb; pdb.set_trace()
        row_descriptions = []
        for value in row[description_rows].values:
            if type(value) is str:
                value = value.replace("\r", "\n")
                value_as_list = value.splitlines()
                descriptions.extend(value_as_list)
                row_descriptions.extend(value_as_list)

        desc_quantity_dict[i] = {"descriptions": row_descriptions}

        row_quantities = []
        for value in row[quantity_rows].values:
            if isinstance(value, (int, float, str)):

                if type(value) is str:
                    value = value.replace("\r", "\n")
                    value_as_list = value.splitlines()
                else:
                    value_as_list = [value]
                # here we need to allow strings for cases like:
                # "5 cases", or "5 boxes" instead of just 5
                row_quantities.extend(value_as_list)

        desc_quantity_dict[i]["quantities"] = row_quantities

    filtered_desc_quantity_list = []

    for _, single_desc_quantity_dict in desc_quantity_dict.items():
        descs = single_desc_quantity_dict["descriptions"]
        quantities = single_desc_quantity_dict["quantities"]

        if len(descs) == 0 or len(quantities) == 0:
            continue

        # TODO: Fix, this assumes that description_rows == quantity_rows (which is not the case always)
        for desc, quantity in zip(descs, quantities):
            if not (isinstance(quantity, str) or isinstance(quantity, (int, float))):
                continue

            extracted_quantity = re.findall(EXTRACT_NUMBERS_REGEX, str(quantity))
            if len(extracted_quantity) != 1:
                continue
            filtered_desc_quantity_list.append(
                (desc, float(extracted_quantity[0]), quantity)
            )

    return filtered_desc_quantity_list
