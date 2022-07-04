import re
from functools import cmp_to_key
from typing import Any, List, Tuple


# Fetching out text from image
def reading_text(img_src):
    import pytesseract as tess
    from PIL import Image

    img = Image.open(img_src)
    bw_img = img.convert("1")
    text = tess.image_to_boxes(bw_img)
    return text


def get_ocr_boxes(tesseract_text: Any):

    boxes = []
    s = []
    char = ""
    for i in range(len(tesseract_text)):
        if tesseract_text[i] == "\n":
            s.append(char)
            char = ""
            boxes.append(s)
            s = []
            continue
        else:
            if tesseract_text[i] == " ":
                s.append(char)
                char = ""
                continue
            else:
                char += tesseract_text[i]

    # seprating top, bottom, left, right
    new_boxes = []
    new_box = []
    prev_box = None
    boxes = [
        (box[0], int(box[1]), int(box[2]), int(box[3]), int(box[4])) for box in boxes
    ]

    for next_box in boxes:
        if prev_box is None:
            prev_box = next_box
            new_box.append(prev_box)
            continue

        # use a per line dynamic value instead of hardcoded
        elif (
            next_box[1] - prev_box[1] < 20
            and prev_box[1] - next_box[1] < 20
            and not (
                next_box[2] > (prev_box[4] + 20) or (next_box[4] + 20) < prev_box[2]
            )
        ):
            new_box.append(next_box)
            prev_box = next_box
            continue

        else:
            new_boxes.append(new_box)
            prev_box = next_box
            new_box = [prev_box]
            continue

    lefts = []
    rights = []
    tops = []
    bottoms = []
    word = ""

    words = []

    for box in new_boxes:
        for text in box:
            lefts.append(text[1])
            rights.append(text[3])
            tops.append(text[2])
            bottoms.append(text[4])
            word += text[0]
        words.append((word, min(lefts), max(tops), max(rights), min(bottoms)))
        lefts = []
        bottoms = []
        tops = []
        rights = []
        word = ""

    def compare_vertical_order(word1, word2):
        if word1[2] < word2[2]:
            return -1
        # using a hardcoded value: 5, might need to finetune
        if word2[2] < word1[2] - 5:
            return 1
        # by default we allow left word to come before right word
        return -1

    sorted_words = sorted(words, key=cmp_to_key(compare_vertical_order))
    sorted_list = sorted_words[::-1]

    # Joining words in the same line
    inner_seq = []
    outer_seq = []
    prev_box = None
    for next_box in sorted_list:
        if prev_box is None:
            prev_box = next_box
            inner_seq.append(next_box)
            continue

        # condition for same line, we might need to finetune
        elif prev_box[1] - next_box[1] <= 5 and not (prev_box[2] - next_box[2] > 20):
            inner_seq.append(next_box)
            prev_box = next_box
            continue

        else:
            outer_seq.append(inner_seq)
            inner_seq = []
            inner_seq.append(next_box)
            prev_box = next_box
            continue

    return outer_seq


def parse_raw_invoice_image(img_src) -> List[Tuple[str, float]]:
    text = reading_text(img_src=img_src)
    ocr_boxes = get_ocr_boxes(text)
    title_row_index, _ = detect_title_row(ocr_boxes=ocr_boxes)
    # items_indices, _ = get_potential_items(ocr_boxes=ocr_boxes)
    items_indices, items = detect_items(ocr_boxes=ocr_boxes)

    result = []

    for i, item in enumerate(items):
        index = items_indices[i]
        item_row = ocr_boxes[index]
        quantity = detect_quantity(
            title_row=ocr_boxes[title_row_index], item_row=item_row
        )
        if not quantity:
            # TODO: The index+1 here refers to the fact that a single item can span multiple rows
            # So ideally we should check all the rows upto a max (of maybe 3/4) until items_indices[i+1]
            if len(ocr_boxes) > index + 1:
                quantity = detect_quantity(
                    title_row=ocr_boxes[title_row_index], item_row=ocr_boxes[index + 1]
                )
        if quantity:
            result.append((item, float(quantity)))

    return result


searchfor = [
    "Quantity",
    "Qty",
    "aty",
    "oty",
    "Amount",
    "Amt",
    "Product",
    "Units",
    "UOM",
    "Rate",
    "Description",
    "HSN",
    "SAC",
    "Tax",
    "CGST",
    "SGST",
    "IGST",
    "Total",
]
regex_title = re.compile("|".join(searchfor), re.IGNORECASE)
regex_description = re.compile("|".join(["Product", "Description"]), re.IGNORECASE)
regex_quantity = re.compile("|".join(["qty", "aty", "oty", "quantity"]), re.IGNORECASE)


def detect_title_row(ocr_boxes: List[List[Tuple[Any]]]):

    ocr_text = list(map(lambda x: list(map(lambda y: y[0], x)), ocr_boxes))

    potential_rows = []
    for row_index, row in enumerate(ocr_text):
        row_string = "".join(row)
        if result := re.findall(regex_title, row_string):
            potential_rows.append((row_index, len(result)))

    if len(potential_rows) == 0:
        return None

    best_row_index = max(potential_rows, key=lambda row: row[1])[0]
    return best_row_index, ocr_text[best_row_index]


# create a better word vocabulary of SKUs
# also in the case of clients, we will have a different word vocab for each client
# and store them in redis?

sku_vocabulary = ["Keya", "Notebook", "Mom", "Shilpa"]
regex_sku_vocabulary = re.compile("|".join(sku_vocabulary), re.IGNORECASE)


@DeprecationWarning
def get_potential_items(ocr_boxes: List[List[Tuple[Any]]]):

    # TODO: Merge
    ocr_text = list(map(lambda x: list(map(lambda y: y[0], x)), ocr_boxes))
    title_row_id, _ = detect_title_row(ocr_boxes)

    if title_row_id is None:
        return None

    item_rows = []
    item_indices = []

    for i, potential_item_row in enumerate(ocr_text[title_row_id + 1 :]):

        if re.search(regex_sku_vocabulary, "".join(potential_item_row)):
            item_indices.append(i + title_row_id + 1)
            item_rows.append(potential_item_row)
        else:
            pass

    return item_indices, item_rows


def detect_items(ocr_boxes: List[List[Tuple[Any]]]):

    title_row_id, _ = detect_title_row(ocr_boxes=ocr_boxes)
    title_row = ocr_boxes[title_row_id]
    description_header_detected = False
    if title_row_id is None:
        return None

    for word_boundary in title_row:
        word = word_boundary[0]
        matches = [m.span() for m in re.finditer(regex_description, word)]
        assert len(matches) <= 1
        if len(matches) == 0:
            continue
        description_start_index, description_end_index = matches[0]
        word_length = len(word)
        word_start_pos, word_end_pos = word_boundary[1], word_boundary[3]
        size_per_character = (word_end_pos - word_start_pos + 1) / word_length
        description_start_pos, description_end_pos = (
            word_boundary[1] + description_start_index * size_per_character,
            word_boundary[1] + description_end_index * size_per_character,
        )
        description_header_detected = True
        break

    if not description_header_detected:
        return []
    # join descriptions from different lines into one
    # str, start_pos, end_pos
    description_rows = []
    for index, item_row in enumerate(ocr_boxes[title_row_id + 1 :]):
        actual_index = index + title_row_id + 1
        for word_boundary in item_row:
            if word_boundary[1] > description_end_pos:
                break
            if word_boundary[3] < description_start_pos:
                continue
            word = word_boundary[0]
            # TODO: For now I assume that there are only one such word (but there could be multiple and we would need to improve upstream or here)
            description_rows.append((actual_index, word_boundary))

    description_groups: List[List[Any]] = []
    description_indices = []
    prev_bottom = None
    for index, description_row in description_rows:
        if prev_bottom is None:
            description_groups.append([description_row[0]])
            description_indices.append(index)
            prev_bottom = description_row[4]
            continue
        current_top = description_row[2]
        # top decreases as we go to the bottom of the page
        if prev_bottom - current_top < 40:
            description_groups[-1].append(description_row[0])
        else:
            description_groups.append([description_row[0]])
            description_indices.append(index)

        prev_bottom = description_row[4]

    joined_description_groups = [
        " ".join(description_group) for description_group in description_groups
    ]
    return description_indices, joined_description_groups


def detect_quantity(title_row, item_row):

    quantity_header_detected = False
    for word_boundary in title_row:
        word = word_boundary[0]
        matches = [m.span() for m in re.finditer(regex_quantity, word)]
        assert len(matches) <= 1
        if len(matches) == 0:
            continue
        quantity_start_index, quantity_end_index = matches[0]
        word_length = len(word)
        word_start_pos, word_end_pos = word_boundary[1], word_boundary[3]
        size_per_character = (word_end_pos - word_start_pos + 1) / word_length
        quantity_start_pos, quantity_end_pos = (
            word_boundary[1] + quantity_start_index * size_per_character,
            word_boundary[1] + quantity_end_index * size_per_character,
        )
        quantity_header_detected = True
        break

    # if we can't detect quantity in title_row, use a different method
    if not quantity_header_detected:
        return None

    number_groups_re = re.compile(r"\d+(?:\.\d+)?")

    # number, start_pos, end_pos
    number_groups = []
    for word_boundary in item_row:

        if word_boundary[1] > quantity_end_pos:
            break
        if word_boundary[3] < quantity_start_pos:
            continue
        word = word_boundary[0]
        matches = [(m.span(), m.group(0)) for m in re.finditer(number_groups_re, word)]
        for match in matches:
            number = match[1]
            number_start_index, number_end_index = match[0]
            word_length = len(word)
            word_start_pos, word_end_pos = word_boundary[1], word_boundary[3]
            size_per_character = (word_end_pos - word_start_pos + 1) / word_length
            number_start_pos, number_end_pos = (
                word_boundary[1] + number_start_index * size_per_character,
                word_boundary[1] + number_end_index * size_per_character,
            )
            number_groups.append((number, number_start_pos, number_end_pos))

    # legible_number_groups =
    best_number = None
    best_distance_from_quantity = quantity_start_pos + quantity_end_pos

    for number, start, end in number_groups:
        distance_from_quantity = abs(start - quantity_start_pos) + abs(
            end - quantity_end_pos
        )
        if distance_from_quantity < best_distance_from_quantity:
            best_number = number
            best_distance_from_quantity = distance_from_quantity

    return best_number
