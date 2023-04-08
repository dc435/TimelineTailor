# ----------------------------------------
# Post processing conducted on data returned from model, but prior to dispaying to user on 'results' html page.
# Primary task is to group events with similar Date+Description into a single result.
# Each event is then displayed as a 'snippet' in a drop-down box on the results page
# ----------------------------------------




from db import Event
from shared_classes import Result, Snippet, DateFormat
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import editdistance

def get_results(
        events: list[Event]
    ) -> list[Result]:

    WIDTH = 140
    TRAILER = "..." 
    SIM_LIMIT = 0.75

    results = []
    date_dict = {}

    for e in events:

        # Build Snippet

        left = TRAILER + e.context_left[-WIDTH:] if len(e.context_left) > WIDTH else TRAILER + e.context_left
        centre = " " + e.ent_text + " "
        right = e.context_right[:WIDTH] + TRAILER if len(e.context_right) > WIDTH else e.context_right + TRAILER

        snippet = Snippet(
            pre = left.replace(e.delimiter,"\n"),
            mid = centre.replace(e.delimiter,"\n"),
            post = right.replace(e.delimiter,"\n")
        )

        display_description = e.description.replace(e.delimiter,"")

        if e.date_format == DateFormat.DMY:
            display_date = e.date_formatted.strftime('%e %B %Y')
        elif e.date_format == DateFormat.MY:
            display_date = e.date_formatted.strftime('%B %Y')
        elif e.date_format == DateFormat.Y:
            display_date = e.date_formatted.strftime('%Y')
        else:
            display_date = "(?)"
        
        # Add Snippet to matching Result, or make new Result?

        added = False
        if display_date in date_dict:
            description_dict = date_dict[display_date]
            for description in description_dict:
                similarity = editdistance_similarity_function(description, display_description)
                if similarity > SIM_LIMIT:
                    index = description_dict[description]
                    results[index].snippets.append(snippet)
                    added = True
                    break
        
        if not added:

            result = Result(
                id="res" + str(len(results) + 1),
                parsed=e.date_success,
                date_text = display_date,
                description= display_description,
                snippets=[snippet],
                date_formatted=e.date_formatted
            )

            results.append(result)
            position_in_res = len(results) - 1
            if display_date in date_dict:
                description_dict = date_dict[display_date]
            else:
                description_dict = {}
            description_dict[e.description] = position_in_res
            date_dict[display_date] = description_dict

    for r in results:
        r.length = len(r.snippets) if len(r.snippets) > 1 else ""

    results.sort(key=lambda r: r.date_text)
    results.sort(key=lambda r: r.date_formatted)

    return results

# Edit distance function used to compare similarity of event descriptions (given they occur on same date):
def editdistance_similarity_function(string1, string2):

    try:
        distance = editdistance.eval(string1, string2)
        similarity = 1 - (distance / max(len(string1), len(string2)))
    except ZeroDivisionError:
        similarity = 0

    return similarity


# Alt similarity function (for testing):
def cos_similarity_function(string1, string2):

    try:
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([string1, string2])

        cosine_similarities = cosine_similarity(vectors)
    except ValueError:
        print("STRING 1:", string1)
        print("STRING 2:", string2)
        return 0

    return cosine_similarities[0][1]
