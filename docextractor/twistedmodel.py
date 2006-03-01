from docextractor import model
from docextractor import ast_pp

class TwistedClass(model.Class):
    def setup(self):
        super(TwistedClass, self).setup()
        self.isinterface = False
        self.implements = []

class TwistedModuleVisitor(model.ModuleVistor):
    def visitCallFunc(self, node):
        current = self.system.current
        if not isinstance(current, model.Class):
            self.default(node)
            return
        str_base = ast_pp.pp(node.node)
        base = self.system.current.dottedNameToFullName(str_base)
        if base == 'zope.interface.implements':
            for arg in node.args:
                current.implements.append(
                    self.system.current.dottedNameToFullName(ast_pp.pp(arg)))
    
class TwistedSystem(model.System):
    Class = TwistedClass
    ModuleVistor = TwistedModuleVisitor

    def finalStateComputations(self):
        super(TwistedSystem, self).finalStateComputations()
        for cls in self.objectsOfType(model.Class):
            if 'zope.interface.Interface' in cls.bases or \
                   'twisted.python.components.Interface' in cls.bases:
                self.markInterface(cls)

    def markInterface(self, cls):
        cls.isinterface = True
        for sc in cls.subclasses:
            self.markInterface(sc)
