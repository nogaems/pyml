# coding: utf-8
import re
import cStringIO
import time
import sys
import traceback
import cPickle
import copy

stdout_block = 0

class Templating:
    def __init__(self, template, request=None):
        self.blocks = 0
        self.path = template
        self.request = request
        self.stock_stdout = sys.stdout
        self.stock_stderr = sys.stderr
        try:
            self.template = open(template).read()
        except:
            print 'Template file \'{)}\' is not found!'.format(template)
            exit(1)
        self.python_code = self.templateParse(self.template)
        if self.python_code is None:
            self.html = self.template
            exit(0)
        self.output = self.executeCode(self.python_code)
        self.blocks = self.outputParse(self.output)
        self.html = self.injectBlocks(self.blocks)

    def templateParse(self, template):
        python_code = re.findall(u'<\?python([.\s\S]+?)\?>', template)
        if python_code != '':
            return python_code
        else:
            return None

    def checkRequest(self, request):
        if isinstance(request, dict):
            to_pickle = request
        else:
            to_pickle = None
        return to_pickle

    def executeCode(self, python_code):
        global stdout_block
        output = cStringIO.StringIO()
        start = time.time()
        while True:
            if stdout_block == False:
                stdout_block = True
                sys.stdout = output
                sys.stderr = output
                code = 'import sys\n'
                if self.request is not None:
                    to_pickle = self.checkRequest(self.request)
                    if to_pickle:
                        code += 'import cPickle\n'
                        dump = cPickle.dumps(to_pickle)
                        code += 'serialized = \"' + dump.encode('string-escape') + '\"\n'
                        code += 'serialized = serialized.decode(\'string_escape\')\n'
                        code += 'query = cPickle.loads(serialized)\n'
                else:
                    code += 'query = None\n'
                for part in python_code:
                    code += 'sys.stdout.write(\'<output>\')\n'
                    code += part
                    code += 'sys.stdout.write(\'</output>\')\n'
                try:
                    exec(code)
                except:
                    traceback.print_exc()
                sys.stdout = self.stock_stdout
                sys.stderr = self.stock_stderr
                stdout_block = False
                return output.getvalue()
            if  time.time() - start > 30:
                return 'script execution time more than 30 seconds'

    def outputParse(self, output):
         return re.findall(u'<output>([.\s\S]*?)</output>', output)

    def injectBlocks(self, blocks):
        temp = self.template
        if  len(blocks) == 0:
            error = '<html><head></head><body>'
            self.output = self.output.replace('<output>', '')
            self.output = self.output.replace('\n', '<br>')
            error += self.output
            error += '</body></html>'
            return error
        temp = temp.replace('<place-for-output>'.encode('utf8'), '')
        for match in re.findall(u'(<\?python(?:[.\s\S]+?)\?>)', temp):
            temp = temp.replace(match, '<place-for-output>'.encode('utf8'))
        for block in blocks:
            block.replace('\n', '<br>')
            temp = temp.replace('<place-for-output>'.encode('utf8'), block, 1)
        return temp

    def save_static(self, html):
        try:
            open(self.path.replace('pyml', 'html'), 'w').write(html)
            return True
        except:
            return False

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print 'Use: pyml.py index.pyml'
        exit(0)
    temp = Templating(sys.argv[1])
    static = temp.save_static(temp.html)
    pass
