##
## Utility functions for handling query results from the text mining provider targeted-assertion knowledge graph
##

from IPython.display import Markdown, display


def printmd(string):
    display(Markdown(string))


SUBJECT_COLOR = "#33FFBD"
OBJECT_COLOR = "#FF0000"
ATTRIBUTE_TYPE_ID = "attribute_type_id"
ATTRIBUTES = "attributes"
VALUE = "value"
BIOLINK_SUBJECT_LOCATION_IN_TEXT = "biolink:subject_location_in_text"
BIOLINK_OBJECT_LOCATION_IN_TEXT = "biolink:object_location_in_text"
BIOLINK_SUPPORTING_TEXT = "biolink:supporting_text"
OFFSET_DELIMITER = "|"


def get_markdown_sentence_with_highlights(
    sentence_text, subject_offsets, object_offsets
):
    """
    Utility function that returns a Markdown representation of the input sentence,
    including colored text for the subject and object spans as indicated in the input arguments.
    """
    first_offsets = subject_offsets
    second_offsets = object_offsets
    first_color = SUBJECT_COLOR
    second_color = OBJECT_COLOR
    if subject_offsets[0] > object_offsets[0]:
        first_offsets = object_offsets
        second_offsets = subject_offsets
        first_color = OBJECT_COLOR
        second_color = SUBJECT_COLOR

    before = sentence_text[0 : first_offsets[0]]
    after = sentence_text[second_offsets[1] :]
    between = sentence_text[first_offsets[1] : second_offsets[0]]
    entity1 = sentence_text[first_offsets[0] : first_offsets[1]]
    entity2 = sentence_text[second_offsets[0] : second_offsets[1]]
    return "{before}{entity1_begin_format}{entity1}{entity1_end_format}{between}{entity2_begin_format}{entity2}{entity2_end_format}{after}".format(
        before=before,
        entity1_begin_format="**<font color='#" + first_color + "'>",
        entity1=entity1,
        entity1_end_format="</font>**",
        between=between,
        entity2_begin_format="**<font color='#" + second_color + "'>",
        entity2=entity2,
        entity2_end_format="</font>**",
        after=after,
    )


def print_sentence(edge_id, supporting_study_results_id, ars_results):
    """
    This function prints a supporting sentence extracted from the input ARS results object.
    The sentence is identified by the edge_id and supporting_study_results_id arguments,
    and contains highlights identifying the subject and object of the assertion.
    """
    attributes_list = ars_results["kp-textmining"]["message"]["knowledge_graph"][
        "edges"
    ][edge_id][ATTRIBUTES]
    supporting_study_result_attributes = next(
        (
            item
            for item in attributes_list
            if item[VALUE] == supporting_study_results_id
        ),
        None,
    )[ATTRIBUTES]

    sentence_text = next(
        (
            item
            for item in supporting_study_result_attributes
            if item[ATTRIBUTE_TYPE_ID] == BIOLINK_SUPPORTING_TEXT
        ),
        None,
    )[VALUE]

    subject_offsets = next(
        (
            item
            for item in supporting_study_result_attributes
            if item[ATTRIBUTE_TYPE_ID] == BIOLINK_SUBJECT_LOCATION_IN_TEXT
        ),
        None,
    )[VALUE].split(OFFSET_DELIMITER)
    subject_offsets = [int(numeric_string) for numeric_string in subject_offsets]

    object_offsets = next(
        (
            item
            for item in supporting_study_result_attributes
            if item[ATTRIBUTE_TYPE_ID] == BIOLINK_OBJECT_LOCATION_IN_TEXT
        ),
        None,
    )[VALUE].split(OFFSET_DELIMITER)
    object_offsets = [int(numeric_string) for numeric_string in object_offsets]

    printmd(
        get_markdown_sentence_with_highlights(
            sentence_text, subject_offsets, object_offsets
        )
    )
