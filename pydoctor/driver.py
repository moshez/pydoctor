from pydoctor import model, html, astbuilder, liveobjectchecker
import sys, os

def error(msg, *args):
    if args:
        msg = msg%args
    print >> sys.stderr, msg
    sys.exit(1)

def findClassFromDottedName(dottedname, optionname):
    # watch out, prints a message and SystemExits on error!
    if '.' not in dottedname:
        error("%stakes a dotted name", optionname)
    parts = dottedname.rsplit('.', 1)
    try:
        mod = __import__(parts[0], globals(), locals(), parts[1])
    except ImportError:
        error("could not import module %s", parts[0])
    try:
        return getattr(mod, parts[1])
    except AttributeError:
        error("did not find %s in module %s", parts[1], parts[0])

def getparser():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option(
        '-c', '--config', dest='configfile',
        help=("Use config from this file (any command line"
              "options override settings from the file)."))
    parser.add_option(
        '-p', '--input-pickle', dest='inputpickle',
        help=("Load the system from this pickle file (default: "
              "none, a blank system is created)."))
    parser.add_option(
        '-o', '--output-pickle', dest='outputpickle',
        help=("Save the system to this pickle file (default: "
              "none, the system is not saved by default)."))
    parser.add_option(
        '--extra-system', action='append', dest='moresystems',
        metavar='SYS:URLPREFIX', default=[],
        help=("Look for objects in this system to.  Links to these objects "
              "will have URLPREFIX prepended to them."))
    parser.add_option(
        '--system-class', dest='systemclass',
        help=("A dotted name of the class to use to make a system."))
    parser.add_option(
        '--builder-class', dest='builderclass',
        help=("A dotted name of the class to use."))
    parser.add_option(
        '--project-name', dest='projectname',
        help=("The project name, appears in the html."))
    parser.add_option(
        '--project-url', dest='projecturl',
        help=("The project url, appears in the html if given."))
    parser.add_option(
        '--testing', dest='testing', action='store_true',
        help=("Don't complain if the run doesn't have any effects."))
    parser.add_option(
        '--pdb', dest='pdb', action='store_true',
        help=("Like py.test's --pdb."))
    parser.add_option(
        '--target-state', dest='targetstate',
        default='finalized', choices=model.states,
        help=("The state to move the system to (default: %default)."))
    parser.add_option(
        '--make-html', action='store_true', dest='makehtml',
        help=("Produce html output."))
    parser.add_option(
        '--add-package', action='append', dest='packages',
        metavar='PACKAGEDIR', default=[],
        help=("Add a package to the system.  Can be repeated "
              "to add more than one package."))
    parser.add_option(
        '--add-module', action='append', dest='modules',
        metavar='MODULE', default=[],
        help=("Add a module to the system.  Can be repeated."))
    parser.add_option(
        '--prepend-package', action='store', dest='prependedpackage',
        help=("Pretend that all packages are within this one.  "
              "Can be used to document part of a package."))
    parser.add_option(
        '--resolve-aliases', action='store_true',
        dest='resolvealiases', default=False,
        help=("This updates references to classes imported from a module "
              "into which they were imported to references to where they "
              "are defined."))
    parser.add_option(
        '--abbreviate-specialcase', action='store',
        dest='abbrevmapping', default='',
        help=("This is a comma seperated list of key=value pairs.  "
              "Where any key corresponds to a module name and value is "
              "the desired abbreviation.  This can be used to resolve "
              "conflicts with abbreviation where you have two or more modules "
              "that start with the same letter.  Example: twistedcaldav=tcd."))
    parser.add_option(
        '--docformat', dest='docformat', action='store', default='epytext',
        help=("Which epydoc-supported format docstrings are assumed to be in."))
    parser.add_option(
        '--html-subject', dest='htmlsubjects', action='append',
        help=("The fullName of object to generate API docs for"
              " (default: everything)."))
    parser.add_option(
        '--html-summary-pages', dest='htmlsummarypages',
        action='store_true', default=False,
        help=("Only generate the summary pages."))
    parser.add_option(
        '--html-write-function-pages', dest='htmlfunctionpages',
        default=False, action='store_true',
        help=("Make individual HTML files for every function and "
              "method. They're not linked to in any pydoctor-"
              "generated HTML, but they can be useful for third-party "
              "linking."))
    parser.add_option(
        '--html-output', dest='htmloutput', default='apidocs',
        help=("Directory to save HTML files to (default 'apidocs')"))
    parser.add_option(
        '--html-writer', dest='htmlwriter',
        help=("Dotted name of html writer class to use (default "
              "'pydoctor.nevowhtml.NevowWriter', requires Divmod Nevow "
              "to be installed)."))
    parser.add_option(
        '--html-viewsource-base', dest='htmlsourcebase',
        help=("This should be the path to the trac browser for the top of the "
              "svn checkout we are documenting part of."))
    parser.add_option(
        '--html-use-sorttable', dest='htmlusesorttable',
        default=False, action="store_true",
        help=("Use the sorttable JS library to make tables of package, "
              "module and class contents sortable"))
    parser.add_option(
        '--html-use-splitlinks', dest='htmlusesplitlinks',
        default=False, action="store_true",
        help=("Generate (unobstrusive) JavaScript to allow class methods to "
              "be shown either in one table per base class or in one big "
              "table."))
    parser.add_option(
        '--html-shorten-lists', dest='htmlshortenlists',
        default=False, action="store_true",
        help=("Generate (unobstrusive) JavaScript to hide some of the "
              "entries in long lists of e.g. subclasses."))
    parser.add_option(
        '-v', '--verbose', action='count', dest='verbosity',
        default=0,
        help=("Be noisier.  Can be repeated for more noise."))
    parser.add_option(
        '-q', '--quiet', action='count', dest='quietness',
        default=0,
        help=("Be quieter."))
    def verbose_about_callback(option, opt_str, value, parser):
        d = parser.values.verbosity_details
        d[value] = d.get(value, 0) + 1
    parser.add_option(
        '--verbose-about', metavar="stage", action="callback",
        type=str, default={}, dest='verbosity_details',
        callback=verbose_about_callback,
        help=("Be noiser during a particular stage of generation."))
    return parser

def readConfigFile(options):
    # this is all a bit horrible.  rethink, then rewrite!
    for i, line in enumerate(open(options.configfile, 'rU')):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            error("don't understand line %d of %s",
                  i+1, options.configfile)
        k, v = line.split(':', 1)
        k = k.strip()
        v = os.path.expanduser(v.strip())

        if not hasattr(options, k):
            error("invalid option %r on line %d of %s",
                  k, i+1, options.configfile)
        pre_v = getattr(options, k)
        if not pre_v:
            if isinstance(pre_v, list):
                setattr(options, k, v.split(','))
            else:
                setattr(options, k, v)
        else:
            if not isinstance(pre_v, list):
                setattr(options, k, v)

def parse_args(args):
    parser = getparser()
    options, args = parser.parse_args(args)
    options.verbosity -= options.quietness
    return options, args

def main(args):
    import cPickle
    options, args = parse_args(args)

    exitcode = 0

    if options.configfile:
        readConfigFile(options)

    try:
        # step 1: make/find the system
        if options.systemclass:
            systemclass = findClassFromDottedName(options.systemclass, '--system-class')
            if not issubclass(systemclass, model.System):
                msg = "%s is not a subclass of model.System"
                error(msg, systemclass)
        else:
            systemclass = model.System

        if options.inputpickle:
            system = cPickle.load(open(options.inputpickle, 'rb'))
            if options.systemclass:
                if type(system) is not systemclass:
                    msg = ("loaded pickle has class %s.%s, differing "
                           "from explicitly requested %s")
                    error(msg, cls.__module__, cls.__name__, options.systemclass)
        else:
            system = systemclass()

        system.options = options

        system.urlprefix = ''
        if options.moresystems:
            moresystems = []
            for fnamepref in options.moresystems:
                fname, prefix = fnamepref.split(':', 1)
                moresystems.append(cPickle.load(open(fname, 'rb')))
                moresystems[-1].urlprefix = prefix
                moresystems[-1].options = system.options
                moresystems[-1].subsystems.append(system)
            system.moresystems = moresystems
        system.sourcebase = options.htmlsourcebase

        if options.abbrevmapping:
            for thing in options.abbrevmapping.split(','):
                k, v = thing.split('=')
                system.abbrevmapping[k] = v

        # step 1.25: make a builder

        if options.builderclass:
            builderclass = findClassFromDottedName(options.builderclass, '--builder-class')
            if not issubclass(builderclass, astbuilder.ASTBuilder):
                msg = "%s is not a subclass of astbuilder.ASTBuilder"
                error(msg, builderclass)
        elif hasattr(system, 'defaultBuilder'):
            builderclass = system.defaultBuilder
        else:
            builderclass = astbuilder.ASTBuilder

        builder = builderclass(system)

        # step 1.5: check that we're actually going to accomplish something here

        if not options.outputpickle and not options.makehtml \
               and not options.testing:
            msg = ("this invocation isn't going to do anything\n"
                   "maybe supply --make-html and/or --output-pickle?")
            error(msg)

        # step 2: add any packages and modules

        if options.packages or options.modules:
            if options.prependedpackage:
                for m in options.prependedpackage.split('.'):
                    builder.pushPackage(m, None)
            for path in options.packages:
                path = os.path.normpath(path)
                if path in system.packages:
                    continue
                if system.state not in ['blank', 'preparse']:
                    msg = 'system is in state %r, which is too late to add new code'
                    error(msg, system.state)
                system.msg('addPackage', 'adding directory ' + path)
                builder.preprocessDirectory(path)
                system.packages.append(path)
            for path in options.modules:
                path = os.path.normpath(path)
                if path in system.packages:
                    continue
                if system.state not in ['blank', 'preparse']:
                    msg = 'system is in state %r, which is too late to add new code'
                    error(msg, system.state)
                system.msg('addModule', 'adding module ' + path)
                # XXX should be a builder method!
                builder.addModule(path)
                system.state = 'preparse'
                system.packages.append(path)
            if options.prependedpackage:
                for m in options.prependedpackage.split('.'):
                    builder.popPackage()

        # step 3: move the system to the desired state

        if not system.packages:
            error("The system does not contain any code, did you "
                  "forget an --add-package?")

        curstateindex = model.states.index(system.state)
        finalstateindex = model.states.index(options.targetstate)

        if finalstateindex < curstateindex and (options.targetstate, system.state) != ('finalized', 'livechecked'):
            msg = 'cannot reverse system from %r to %r'
            error(msg, system.state, options.targetstate)

        if finalstateindex > 0 and curstateindex == 0:
            msg = 'cannot advance totally blank system to %r'
            error(msg, options.targetstate)

        def liveCheck():
            liveobjectchecker.liveCheck(system, builder)

        funcs = [None,
                 builder.analyseImports,
                 builder.extractDocstrings,
                 builder.finalStateComputations,
                 liveCheck]

        for i in range(curstateindex, finalstateindex):
            f = funcs[i]
            system.msg(f.__name__, f.__name__)
            f()

        if system.state != options.targetstate:
            msg = "failed to advance state to %r (this is a bug)"
            error(msg, options.targetstate)

        if system.options.projectname is None:
            name = '/'.join([ro.name for ro in system.rootobjects])
            system.msg('warning', 'WARNING: guessing '+name+' for project name', thresh=-1)
            system.guessedprojectname = name

        # step 4: save the system, if desired

        if options.outputpickle:
            del system.options # don't persist the options
            f = open(options.outputpickle, 'wb')
            cPickle.dump(system, f, cPickle.HIGHEST_PROTOCOL)
            f.close()
            system.options = options

        # step 5: make html, if desired

        if options.makehtml:
            if options.htmlwriter:
                writerclass = findClassFromDottedName(options.htmlwriter, '--html-writer')
            else:
                from pydoctor import nevowhtml
                writerclass = nevowhtml.NevowWriter

            system.msg('html', 'writing html to %s using %s.%s'%(
                options.htmloutput, writerclass.__module__, writerclass.__name__))

            writer = writerclass(options.htmloutput)
            writer.system = system
            writer.prepOutputDirectory()

            if options.htmlsubjects:
                subjects = []
                for fn in options.htmlsubjects:
                    subjects.append(system.allobjects[fn])
            elif options.htmlsummarypages:
                writer.writeModuleIndex(system)
                subjects = []
            else:
                writer.writeModuleIndex(system)
                subjects = system.rootobjects
            writer.writeIndividualFiles(subjects, options.htmlfunctionpages)
            if system.epytextproblems:
                def p(msg):
                    system.msg('epytext', msg, thresh=-1, topthresh=1)
                p("these objects' docstrings are not proper epytext:")
                exitcode = 2
                for fn in system.epytextproblems:
                    p('    '+fn)
    except:
        if options.pdb:
            import pdb
            pdb.post_mortem(sys.exc_traceback)
        raise
    return exitcode

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
