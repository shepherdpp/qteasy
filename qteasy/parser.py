# coding=utf-8
# parser.py

# ======================================
# This file contains a blender parser
# that can be used to parse user defined
# signal blender strings and execute
# their values, which are signals
# combined by all output signals from 
# all operator strategies
# ======================================

class Parser:
    def __init__(self, string, vars={}):
        self.string = string
        self.index = 0
        self.vars = {
            'pi': 3.141592653589793,
            'e':  2.718281828459045
        }
        for var in vars.keys():
            if self.vars.get(var) != None:
                raise Exception("Cannot redefine the value of " + var)
            self.vars[var] = vars[var]

    def get_value(self):
        value = self.parse_expression()
        self.skip_whitespace()
        if self.has_next():
            raise Exception(
                    "Unexpected character found: '" +
                    self.peek() +
                    "' at index " +
                    str(self.index))
        return value

    def peek(self):
        return self.string[self.index:self.index + 1]

    def has_next(self):
        return self.index < len(self.string)

    def skip_whitespace(self):
        while self.has_next():
            if self.peek() in ' \t\n\r':
                self.index += 1
            else:
                return

    def parse_expression(self):
        return self.parse_add_minus()

    def parse_add_minus(self):
        values = [self.parse_multi_div()]
        while True:
            self.skip_whitespace()
            char = self.peek()
            if char == '+':
                self.index += 1
                values.append(self.parse_multi_div())
            elif char == '-':
                self.index += 1
                values.append(-1 * self.parse_multi_div())
            else:
                break
        return sum(values)

    def parse_multi_div(self):
        values = [self.parse_parenthesis()]
        while True:
            self.skip_whitespace()
            char = self.peek()
            if char == '*':
                self.index += 1
                values.append(self.parse_parenthesis())
            elif char == '/':
                div_index = self.index
                self.index += 1
                denominator = self.parse_parenthesis()
                if denominator == 0:
                    raise Exception(
                            "Division by 0 kills baby whales (occured at index " +
                            str(div_index) +
                            ")")
                values.append(1.0 / denominator)
            else:
                break
        value = 1.0
        for factor in values:
            value *= factor
        return value

    def parse_parenthesis(self):
        self.skip_whitespace()
        char = self.peek()
        if char == '(':
            self.index += 1
            value = self.parse_expression()
            self.skip_whitespace()
            if self.peek() != ')':
                raise Exception(
                        "No closing parenthesis found at character "
                        + str(self.index))
            self.index += 1
            return value
        else:
            return self.parse_negative()

    def parse_negative(self):
        self.skip_whitespace()
        char = self.peek()
        if char == '-':
            self.index += 1
            return -1 * self.parse_parenthesis()
        else:
            return self.parseValue()

    def parseValue(self):
        self.skip_whitespace()
        char = self.peek()
        if char in '0123456789.':
            return self.parse_number()
        else:
            return self.parse_variable()

    def parse_variable(self):
        self.skip_whitespace()
        var = ''
        while self.has_next():
            char = self.peek()
            if char.lower() in '_abcdefghijklmnopqrstuvwxyz0123456789':
                var += char
                self.index += 1
            else:
                break

        value = self.vars.get(var, None)
        if value == None:
            raise Exception(
                    "Unrecognized variable: '" +
                    var +
                    "'")
        return float(value)

    def parse_number(self):
        self.skip_whitespace()
        strValue = ''
        decimal_found = False
        char = ''

        while self.has_next():
            char = self.peek()
            if char == '.':
                if decimal_found:
                    raise Exception(
                            "Found an extra period in a number at character " +
                            str(self.index) +
                            ". Are you European?")
                decimal_found = True
                strValue += '.'
            elif char in '0123456789':
                strValue += char
            else:
                break
            self.index += 1

        if len(strValue) == 0:
            if char == '':
                raise Exception("Unexpected end found")
            else:
                raise Exception(
                        "I was expecting to find a number at character " +
                        str(self.index) +
                        " but instead I found a '" +
                        char +
                        "'. What's up with that?")

        return float(strValue)


def blender_evaluate(expression, vars={}):
    try:
        p = Parser(expression, vars)
        value = p.get_value()
    except Exception as ex:
        msg = ex.message
        raise Exception(msg)

    # Return an integer type if the answer is an integer 
    if int(value) == value:
        return int(value)

    # If Python made some silly precision error 
    # like x.99999999999996, just return x + 1 as an integer 
    epsilon = 0.0000000001
    if int(value + epsilon) != int(value):
        return int(value + epsilon)
    elif int(value - epsilon) != int(value):
        return int(value)
    return value