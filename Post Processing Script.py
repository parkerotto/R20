"""
Model exported as python.
Name : Post Processing
Group : 
With QGIS : 33602
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProcessingParameterFeatureSink
import processing


class PostProcessing(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterVectorLayer('polygonized', 'Polygonized', types=[QgsProcessing.TypeVectorPolygon], defaultValue=None))
        self.addParameter(QgsProcessingParameterFeatureSink('Postprocessed', 'Postprocessed', type=QgsProcessing.TypeVectorAnyGeometry, createByDefault=True, supportsAppend=True, defaultValue=None))

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(5, model_feedback)
        results = {}
        outputs = {}

        # Delete holes
        alg_params = {
            'INPUT': parameters['polygonized'],
            'MIN_AREA': 0,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['DeleteHoles'] = processing.run('native:deleteholes', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': 1.3,
            'END_CAP_STYLE': 2,  # Square
            'INPUT': outputs['DeleteHoles']['OUTPUT'],
            'JOIN_STYLE': 1,  # Miter
            'MITER_LIMIT': 2000,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Simplify
        alg_params = {
            'INPUT': outputs['Buffer']['OUTPUT'],
            'METHOD': 2,  # Area (Visvalingam)
            'TOLERANCE': 0.5,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Simplify'] = processing.run('native:simplifygeometries', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(3)
        if feedback.isCanceled():
            return {}

        # Buffer
        alg_params = {
            'DISSOLVE': False,
            'DISTANCE': -1.3,
            'END_CAP_STYLE': 2,  # Square
            'INPUT': outputs['Simplify']['OUTPUT'],
            'JOIN_STYLE': 1,  # Miter
            'MITER_LIMIT': 2000,
            'SEGMENTS': 5,
            'SEPARATE_DISJOINT': True,
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Buffer'] = processing.run('native:buffer', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(4)
        if feedback.isCanceled():
            return {}

        # Orthogonalize
        alg_params = {
            'ANGLE_TOLERANCE': 15,
            'INPUT': outputs['Buffer']['OUTPUT'],
            'MAX_ITERATIONS': 1000,
            'OUTPUT': parameters['Postprocessed']
        }
        outputs['Orthogonalize'] = processing.run('native:orthogonalize', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Postprocessed'] = outputs['Orthogonalize']['OUTPUT']
        return results

    def name(self):
        return 'Post Processing'

    def displayName(self):
        return 'Post Processing'

    def group(self):
        return ''

    def groupId(self):
        return ''

    def createInstance(self):
        return PostProcessing()
