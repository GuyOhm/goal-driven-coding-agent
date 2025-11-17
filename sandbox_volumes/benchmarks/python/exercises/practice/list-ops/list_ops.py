def append(list1, list2):
    result = []
    # add elements from first list
    i = 0
    while i < len(list1):
        result.append(list1[i])
        i += 1
    # add elements from second list
    j = 0
    while j < len(list2):
        result.append(list2[j])
        j += 1
    return result


def concat(lists):
    result = []
    i = 0
    while i < len(lists):
        sub = lists[i]
        j = 0
        while j < len(sub):
            result.append(sub[j])
            j += 1
        i += 1
    return result


def filter(function, list):
    result = []
    i = 0
    while i < len(list):
        item = list[i]
        if function(item):
            result.append(item)
        i += 1
    return result


def length(list):
    count = 0
    i = 0
    while i < len(list):
        count += 1
        i += 1
    return count


def map(function, list):
    result = []
    i = 0
    while i < len(list):
        result.append(function(list[i]))
        i += 1
    return result


def foldl(function, list, initial):
    acc = initial
    i = 0
    while i < len(list):
        acc = function(acc, list[i])
        i += 1
    return acc


def foldr(function, list, initial):
    acc = initial
    i = len(list) - 1
    while i >= 0:
        acc = function(acc, list[i])
        i -= 1
    return acc


def reverse(list):
    result = []
    i = len(list) - 1
    while i >= 0:
        result.append(list[i])
        i -= 1
    return result
