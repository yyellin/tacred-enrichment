from collections import defaultdict


class MapTokenization(object):
    """
    'MapTokenization' exposes one static method - map_a_to_b - that accepts two token lists - list_a and
    list_b, which  potentially  reflect different tokenizations of the same sentences. So for example,
    the sentence 'This rock-hard cake is awful' could be tokenized as either:
       a) 1: This
          2: rock-hard
          3. cake
          4. is
          5. awful
    or
       b) 1: This
          2: rock
          3: -
          3: hard
          4: cake
          5: is
          6. awful
    'map_a_to_b' will return a dictionary of lists in which each index in list_a is mapped to a list
    of corresponding indices in list_b.

    """

    @staticmethod
    def map_a_to_b(list_a, list_b):

        lookup = defaultdict(list)

        index_a = 1
        index_b = 1

        while index_a <= len(list_a) and index_b <= len(list_b):

            # Possibility 1: pointing to same token
            if list_a[index_a - 1] == list_b[index_b - 1]:
                lookup[index_a].append(index_b)

                index_a += 1
                index_b += 1
                continue

            # Possibility 2: b's token represents multiple different tokens in a
            #

            a_is_substring = False
            word_b = list_b[index_b - 1]
            while list_a[index_a - 1] in word_b:
                a_is_substring = True

                lookup[index_a].append(index_b)

                index_a += 1
                if index_a > len(list_a):
                    break

            if a_is_substring:
                index_b += 1
                continue

            # Possibility 3: a's token represents multiple different tokens in b
            #

            b_is_substring = False
            word_a = list_a[index_a - 1]
            while list_b[index_b - 1] in word_a:
                b_is_substring = True

                lookup[index_a].append(index_b)

                index_b += 1
                if index_b > len(list_b):
                    break

            if b_is_substring:
                index_a += 1
                continue

            # Fallback: increment index of b until a match with a is found
            while index_b < len(list_b):

                tmp = index_a
                found = False
                while tmp < len(list_a):
                    if list_a[tmp - 1] == list_b[index_b - 1]:
                        found = True
                        break
                    tmp += 1

                if found:
                    index_a = tmp
                    break

                index_b += 1

        return lookup
