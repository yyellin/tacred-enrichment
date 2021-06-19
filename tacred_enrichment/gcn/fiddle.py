from tacred_enrichment.internal.core_nlp_client import CoreNlpClient


sentence = 'Fifty -six bottles of pop on the wall'
sentence = 'Tom Thabane resigned in October last year to form the All Basotho Convention (ABC), crossing the floor with 17 members of parliament, causing constitutional monarch King Letsie III to dissolve parliament and call the snap election.'


tokens = ["Palin", "'s", "two", "months", "in", "the", "national", "media", "spotlight", "raised", "questions", "about", "some", "of", "her", "activities", "as", "governor", "-", "in", "particular", ",", "her", "charging", "the", "state", "$", "17,000", "in", "per", "diem", "payments", "for", "nights", "she", "stayed", "in", "her", "Wasilla", "home", ",", "and", "$", "21,000", "for", "her", "children", "'s", "travel.No", "new", "policies", "have", "been", "set", "for", "those", "practices", ",", "McAllister", "said", "Tuesday", "."]
tokens = ["The", "Frontlines", "<", "http://freedomtoserve.blogspot.com/", ">", ",", "the", "blog", "for", "the", "Servicemembers", "Legal", "Defense", "Network", ",", "has", "been", "doing", "a", "series", "on", "the", "gay", "community", "who", "have", "served", "our", "country", "in", "the", "military", "titled", "`", "Honor", "Every", "Veteran", "<", "http://freedomtoserve.blogspot.com/search/label/honor%20every%20veteran", ">", ".", "'"]

tokens = ["Palin", "'s", "two", "months", "in", "the", "national", "media", "spotlight", "raised", "questions", "about", "some", "of", "her", "activities", "as", "governor", "-", "in", "particular", ",", "her", "charging", "the", "state", "$", "17,000", "in", "per", "diem", "payments", "for", "nights", "she", "stayed", "in", "her", "Wasilla", "home", ",", "and", "$", "21,000", "for", "her", "children", "'s", "travel", ".", "George", "was", "also", "an", "idiot", "and", "he", "too", "generally", "made", "no", "sense", "."]

sentence = 'Last week Spencer claimed he purchased 3,000 copies of the Playboy issue featuring his partner Heidi Montag . This week Spencer Pratt claims the number is closer to 5000 .'

sentence = 'In a statement, Rep. Maxine Waters, D-Calif., who holds the seat Hawkins vacated, called him "the author of some of the most significant legislation ever passed in the House" ... particularly in the areas of education and labor.'


#tokens = ["The", "Jerusalem", "Foundation", ",", "a", "charity", "founded", "by", "Kollek", "40", "years", "ago", ",", "said", "he", "died", "of", "natural", "causes", "."]


core_nlp = CoreNlpClient('localhost', 9000, 15000)

def split_keep_delimiter(tokens):

    fix_tokens = []

    for token in tokens:
        subtokens = token.split('.')

        if len(subtokens) == 1:
            fix_tokens.append(token)

        else:
            fix_tokens.append(subtokens[0])

            for subtoken in subtokens[1:]:
                fix_tokens.append('.')
                fix_tokens.append(subtoken)

    return fix_tokens



    #return [item for token in tokens for subtoken in token.split('.') for item in [subtoken, '.'] ]


sentence  = "After graduation Johnny transitioned to full-time research"

parse = core_nlp.get_deps(sentence)

sentence_adj = [0]
for sentence in parse['sentences'][:-1]:
    sentence_adj.append(len(sentence['tokens']))

for coref in parse['corefs'].values():
    #anchor = next((x['startIndex']+x['sentNum'], x['endIndex']+x['sentNum']) for x in coreference if x['isRepresentativeMention'])
    #ref = [(x['startIndex']+x['sentNum'], x['endIndex']+x['sentNum']) for x in coreference if not x['isRepresentativeMention']]
    anchor = next(x for x in coref if x['isRepresentativeMention'])
    refs = [x for x in coref if not x['isRepresentativeMention']]

    anchor_coords = [anchor['startIndex'] + sentence_adj[anchor['sentNum'] - 1], \
                     anchor['endIndex'] + sentence_adj[anchor['sentNum'] - 1]]

    refs_coords = [[ref['startIndex'] + sentence_adj[ref['sentNum'] - 1], \
                    ref['endIndex'] + sentence_adj[ref['sentNum'] - 1]] for ref in refs]

    print(anchor_coords, refs_coords)


wait_here = True