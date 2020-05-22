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
                lookup[index_a - 1].append(index_b - 1)

                index_a += 1
                index_b += 1
                continue


            # Possibility 2: b's token represents multiple different tokens in a
            #

            a_is_substring = False
            word_b = list_b[index_b - 1]
            while word_b.startswith(list_a[index_a - 1]):
                a_is_substring = True

                lookup[index_a - 1].append(index_b - 1)
                word_b = word_b[len(list_a[index_a - 1]):]

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
            while word_a.startswith(list_b[index_b - 1]):
                b_is_substring = True

                lookup[index_a - 1].append(index_b - 1)
                word_a = word_a[len(list_b[index_b - 1]):]

                index_b += 1
                if index_b > len(list_b):
                    break

            if b_is_substring:
                index_a += 1
                continue

            # Fallback: increment index of b until a match with a is found
            while index_b <= len(list_b):

                tmp = index_a
                found = False
                while tmp <= len(list_a):
                    if list_a[tmp - 1] == list_b[index_b - 1]:
                        found = True
                        break
                    tmp += 1

                if found:
                    index_a = tmp
                    break

                index_b += 1


        return lookup

    @staticmethod
    def check_defined(lookup, list_a):
        defined = {list_a_element: True for list_a_element in lookup.keys()}

        if (len(defined) != len(list_a)) \
                or (0 not in defined) \
                or ((len(defined) - 1) not in defined):
            return False

        return True

    @staticmethod
    def check_surjectivity(lookup, list_b):
        coverage = {list_b_element: True for list_b_elements in lookup.values() for list_b_element in list_b_elements}

        if (len(coverage) != len(list_b)) \
                or (0 not in coverage) \
                or ((len(coverage) - 1) not in coverage):
            return False

        return True
