
from schema import Schema, And, Use, Or, Optional, Forbidden, SchemaError, Regex
import sys, os
import frontmatter
#print( os.path.dirname(os.path.abspath(__file__)) + '/reeco-annotation-schema/' )
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)) + '/reeco-annotation-schema/')
from reeco import Schema as ReecoSchema

class Validator:
    def __init__(self):
        REECO = ReecoSchema()
        #print("Components: ",REECO.components())
        components = list(map( lambda x: x['type'], REECO.components() ) ) + ['Component'] 
        containers = list(map( lambda x: x['type'], REECO.containers() ) ) + ['Container']
        licences = list(map( lambda x: x['code'], REECO.licences() ) )
        print(licences)
        ## Reusable validators
        validateURL = And(str, Regex('^http[s]?://.+$'), error='Value must be an HTTP(S) URL' )
        validateID = And(str, Regex('[^\s]+(/[^\s]+(/[^\s]+)?)?') )

        ## Validators for both containers and components
        both = [
            {Or("component-id", "container-id", only_one=True): str}
        ]
        self._containerValidators = [] + both + [
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
        self._componentValidators = [] + both + [
            # component-id
            {'component-id': validateID },
            {Forbidden('container-id'): object },
            # resource
            {Optional('resource'): str},
            # doi
            {Optional('doi'): And(str, Regex('^http[s]?://.+$') )}, 
            # name
            {'name': And(str, error="This annotation should include a short name, as a single value")},
            # description
            {'description': And(str, error="This annotation should include a description, as a single paragraph")},
            # type
            {'type': And(lambda v: v in components, error='Type must be one of: ' + ", ".join(components) )},
            # release-date
            {Optional('release-date'): str},
            # release-number
            {Optional('release-date'): str},
            # release-link
            {Optional('release-link'): validateURL},
            # changelog
            ### TODO Check file exists
            # licence
            {'licence': And(lambda v: v in licences, error='Licence must be a list of licence codes from the Reeco Annotation Schema reference.' )},
            # image
            # logo
            # demo
            # running-instance
            # contributors
            # related-component
            # informed-by
            # use-case
            # story
            # persona
            # documentation
            # evaluated-in
            # extends-software
            # reuses-software
            # reuses-data
            # serves-data
            # produces-data
            # reused-in
            # generated-by
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
        return self._validate(annotations, self._componentValidators)
    
    def asContainer(self, annotations):
        return self._validate(annotations, self._containerValidators)
    
    
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