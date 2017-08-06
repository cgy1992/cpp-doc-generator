import argparse
from enum import Enum


class tags(Enum):
    METHOD = 'method'
    FUNCTION = 'function'
    CLASS = 'class'
    NAMESPACE = 'namespace'
    CONSTRUCT = 'construct'


class comments:

    def __init__(self, comment_lines):
        self.comment_lines = comment_lines
        pre_processed_comments = []
        for each_line in self.comment_lines:
            each_line = each_line.strip('*/ \t\n')
            if each_line:
                pre_processed_comments.append(each_line)
        self.comment_lines = pre_processed_comments

    def process(self):
        '''
        Process the comments and retrieve info from them
        '''
        temp = ''.join(self.comment_lines).split('@')
        properties = dict()

        # INFO: FOR NOW PARSING ONLY METHODS AND FUNCS
        first_space_pos = temp[1].find(' ')
        if temp[1][:first_space_pos] == tags.METHOD.value:
            properties['is_what'] = tags.METHOD.value
            properties['access'] = temp[2][temp[2].find(' ') + 1:]
        elif temp[1][:first_space_pos] == tags.FUNCTION.value:
            properties['is_what'] = tags.FUNCTION.value
        elif temp[1][:first_space_pos] == tags.CONSTRUCT.value:
            properties['is_what'] = tags.CONSTRUCT.value
        else:
            return False

        if properties['is_what'] == tags.METHOD.value or properties['is_what'] == tags.FUNCTION.value or properties['is_what'] == tags.CONSTRUCT.value:
            properties['params'] = []
            properties['returns'] = None
            for each_portion in temp:
                # TODO: Add code for desc block too.
                if each_portion.startswith('param'):
                    data = each_portion[each_portion.find(
                        'param') + len('param') + 1:]
                    properties['params'].append(data)

                elif each_portion.startswith('returns'):
                    data = each_portion[each_portion.find(
                        'returns') + len('returns') + 1:]
                    properties['returns'] = data
        return properties

    def __str__(self):
        COMMENT_TAG = "=" * 10 + "COMMENT" + "=" * 10 + '\n'
        return self.COMMENT_TAG + '\n'.join(self.comment_lines)


class code:

    def __init__(self, code_lines):
        self.code_lines = code_lines

    def process(self):
        pass

    def __str__(self):
        CODE_TAG = "." * 10 + "CODE" + "." * 10 + '\n'
        return self.CODE_TAG + '\n'.join(self.code_lines)


class segment:

    def __new__(segment, comment_lines, code_lines):
        temp_comm = comments(comment_lines)
        res = temp_comm.process()
        if res is not False:
            return object.__new__(segment)
        else:
            return None

    def __init__(self, comment_lines, code_lines):
        self.__comm = comments(comment_lines)
        self.__code = code(code_lines)
        res = self.__comm.process()
        print(" res is: ", res)
        self.is_what = res['is_what']
        if self.is_what == tags.FUNCTION.value or self.is_what == tags.METHOD.value or self.is_what == tags.CONSTRUCT.value:
            if self.is_what == tags.METHOD.value:
                self.access = res['access']
            self.params = res['params']
            self.ret_val = res['returns']

    def __str__(self):
        return self.__comm.__str__() + "\n" + self.__code.__str__()

    def __repr__(self):
        return self.__str__()


class parser():
    def __init__(self):
        self.segments = []
        # self.file_name = file_name

    def __order_segments(self, segments_list):
        # segments_list is supposed to be a list of triplets of integers like this:
        # [(1, 0, 14), (3, 0, 4), (2, 0, 7), (16, 0, 17), (15, 0, 18),
        #                (10, 0,13), (5,0, 6), (8,0, 9), (11, 0,12)]
        # Each triplet denoting (comm_start, comm_end, segment_end)
        limit = max([max(e) for e in segments_list]) + 1
        segments_list.append((-1, -1, limit,))
        segments_list.sort(key=lambda ele: ele[0])

        def core_order_segments(passed_idx):
            # TODO: Fix extra appends at the end of list
            current_tuple = segments_list[passed_idx]
            next_idx = passed_idx + 1
            while next_idx < len(segments_list):
                curr_pair_ans = []
                while current_tuple[0] < segments_list[next_idx][0] and segments_list[next_idx][2] < current_tuple[2]:
                    res = core_order_segments(next_idx)
                    if res is not None:
                        next_idx, temp_answer = res
                        curr_pair_ans.append(temp_answer)
                    else:
                        curr_pair_ans.append(
                            dict({segments_list[next_idx]: []}))
                        break
                return next_idx, dict({current_tuple: (curr_pair_ans)})
            return None

        return core_order_segments(0)

    def parse(self, file_name):

        # TODO: Remove any blank line from the file
        # TODO: Parse file char by char instead of line by line
        self.segments = []
        comm_start = None
        comm_end = None
        comm_and_open_paren = []

        with open(file_name) as f:
            src = f.readlines()
            for line_num, line in enumerate(src):
                line = line.strip()
                if line.startswith("/**"):
                    comm_start = line_num
                    comm_end = None

                if line.startswith("*/"):
                    comm_end = line_num

                if not(comm_start is not None and comm_end is None):
                    if ';' in line:
                        if comm_start is not None and comm_end is not None:
                            self.segments.append(
                                (comm_start, comm_end, comm_end + 1))
                            comm_start = None
                            comm_end = None

                    if '{' in line:
                        comm_and_open_paren.append(
                            (comm_start, comm_end, line_num,))
                        comm_start = None
                        comm_end = None

                    if '}' in line:
                        possible_match = comm_and_open_paren.pop()
                        if possible_match[0] is not None and possible_match[1] is not None:
                            self.segments.append(
                                (possible_match[0], possible_match[1], line_num,))

            temp = []
            for each_segment in self.segments:
                comm = src[each_segment[0]: each_segment[1] + 1]
                code = src[each_segment[1] + 1: each_segment[2] + 1]
                obj = segment(comm, code)
                if obj is not None:
                    temp.append(obj)
            self.segments = temp
        return self.segments


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description="Cpp doc generator")
    arg_parser.add_argument(
        "-f", nargs='+', required=True, metavar="file_names", dest="files")
    src_files = arg_parser.parse_args().files

    p = parser()
    for each_file in src_files:
        segments = p.parse(each_file)
        print("segments for file: ", each_file, "are: ")
        for each_segment in segments:
            print(each_segment)
