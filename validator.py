import re
import requests
from schema import Schema, And, Use, Or, Optional, Forbidden, SchemaError, Regex
import sys, os
import frontmatter
#print( os.path.dirname(os.path.abspath(__file__)) + '/reeco-annotation-schema/' )
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/reeco-annotation-schema/')
from reeco import Schema as ReecoSchema


class Validator:
    def __init__(self):
        reeco_schema_link = "https://github.com/reeco-framework/reeco-annotation-schema/blob/main/schema/README.md"
        REECO = ReecoSchema()
        #print("Components: ",REECO.components())
        components = list(map( lambda x: x['type'], REECO.components() ) ) + ['Component'] 
        containers = list(map( lambda x: x['type'], REECO.containers() ) ) + ['Container']
        licences = list(map( lambda x: x['code'], REECO.licences() ) )
        #print(licences)
        ## Reusable validators
        validateURL = And(str, Regex('^http[s]?://.+$'), error='Value must be an HTTP(S) URL' )
        validateID = And(str, Regex('[^\s]+(/[^\s]+(/[^\s]+)?)?') )

        def resolve(data):
            response = requests.head(data)
            if response.status_code == 200:
                return data
            else:
                raise Exception("URL cannot be resolved")

        resolvableURL = And(Use(lambda fff: resolve(fff)), error="URL cannot be resolved.")

        ## Validators for both containers and components
        both = [
            {Or("component-id", "container-id", only_one=True): str}
        ]
        self._containerErrors = [] + both + [
        ## Mandatory items for containers
        # name
        {'name': str},
        {'type': And(lambda v: v in containers, error='Type must be one of: ' + ", ".join(containers) )},
        # container-id
        {'container-id': validateID},
        # funder [CHECK]
        {Optional('funder'): list},
        #         And(
        #             list, [ { Optional('name'): str,
        #                 Optional('url'): str,
        #                 Optional('grant-agreement'): str} ] }},
        # has-part
        {'has-part': list},
        # ro-crate
        {Optional('ro-crate'): list}
        ]
        #print(licences)
        self._componentErrors = [] + both + [
            # component-id
            {'component-id': validateID },
            {Forbidden('container-id'): object },
            # resource
            {Optional('resource'): str},
            # doi https://www.crossref.org/blog/dois-and-matching-regular-expressions/
            # /^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i
            # /^10.1002/[^\s]+$/i
            # /^10.\d{4}/\d+-\d+X?(\d+)\d+<[\d\w]+:[\d\w]*>\d+.\d+.\w+;\d$/i
            # /^10.1021/\w\w\d++$/i
            # /^10.1207/[\w\d]+\&\d+_\d+$/i
            {Optional('doi'): And(str,
                    Or(
                        Regex(r'^10.\d{4,9}/[-._;()/:A-Z0-9]+$', re.I),
                        Regex(r'^10.1002/[^\s]+$', re.I),
                        Regex(r'^10.\d{4}/\d+-\d+X?(\d+)\d+<[\d\w]+:[\d\w]*>\d+.\d+.\w+;\d$', re.I),
                        #Regex(r'^10.1021/\w\w\d++$', re.I), These two don't seem to work
                        #Regex(r'^10.1207/[\w\d]+\&\d+_\d+$', re.I),
                        error="DOI is invalid"
                    ))},
            # name
            {'name': And(str, error="This annotation should include a short name, as a single value")},
            # description
            {'description': And(str, error="This annotation should include a description, as a single paragraph")},
            # type
            {'type': And(lambda v: v in components, error='Type must be one of: ' + ", ".join(components) )},
            # release-date
            {Optional('release-date'): str},
            # release-number
            {Optional('release-number'): str},
            # release-link
            {Optional('release-link'): And(validateURL, resolvableURL)},
            # changelog ### TODO Check file exists
            {Optional('changelog'): str},
            # licence
            {'licence': [And(str, lambda v: v in licences, error='Licence must be a list of licence codes from the Reeco Annotation Schema reference.' )]},
            # image
            {Optional('image'): And(validateURL, resolvableURL)},
            # logo
            {Optional('logo'): And(validateURL, resolvableURL)},
            # demo
            {Optional('demo'): And(validateURL, resolvableURL)},
            # running-instance
            {Optional('running-instance'): And(validateURL, resolvableURL)},
            # contributors
            {Optional('contributors'): list},
            # related-component
            {'related-components': [And({
                # informed-by
                Optional('informed-by'): Or(str, list),
                # use-case
                Optional('use-case'): Or(str, list),
                # story
                Optional('story'): Or(str, list),
                # persona
                Optional('persona'): Or(str, list),
                # documentation
                Optional('documentation'): Or(str, list),
                # evaluated-in
                Optional('evaluated-in'): Or(str, list),
                # extends-software
                Optional('extends'): Or(str, list),
                # reuses-software
                Optional('reuses'): Or(str, list),
                # serves-data
                Optional('serves-data'): Or(str, list),
                # produces-data
                Optional('produces-data'): Or(str, list),
                # reused-in
                Optional('reused-in'): Or(str, list),
                # generated-by
                Optional('generated-by'): Or(str, list)
            }, error="Invalid values")]},

            # bibliography
            # published-in
            # main-publication
            # main-report
            # deliverable-document
            # work-package
            # pilot
            # project
        ]
        
        
    
    def _validate(self, annotations, validators):
        errors = []
        #print(validators)
        for attribute in validators:
            try:
                schema = Schema(attribute, ignore_extra_keys=True)
                schema.validate(annotations)
            except Exception as e:
                #print(type(e))
                #print(dir(e))
                #print('args',e.args)
                #print('autos',e.autos)
                #print('code',e.code)
                #print('errors',e.errors)
                errors.append(e)
        return errors
    
    def asComponent(self, annotations):
        return {'error': self._validate(annotations, self._componentErrors)}
    
    def asContainer(self, annotations):
        return {'error': self._validate(annotations, self._containerErrors)}
    
    
if __name__ == '__main__':
    if len( sys.argv ) < 2:
        print ("You must set argument!!!")
        exit(1)
    V = Validator()
    print('File: ' + sys.argv[1])
    report = []
    with open(sys.argv[1]) as f:
        try:
            annotations, content = frontmatter.parse(f.read())
            ## Start validation
            if 'component-id' in annotations.keys():
                ### Validate as component
                report = V.asComponent(annotations)
            elif 'container-id' in annotations.keys():
                ### Validate as container
                report = V.asContainer(annotations)
        except Exception as e:
            # Malformed YAML in Markdown
            report = report + [e]
    print(report)