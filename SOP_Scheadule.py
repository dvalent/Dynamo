import clr
import sys
import System
import math


clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.GeometryConversion)

from System.Collections.Generic import *

clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
from Autodesk.Revit.DB.Analysis import *

clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *


clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
from System.Collections.Generic import *
from Autodesk.Revit.DB.Structure import *

clr.AddReference("RevitNodes")
clr.ImportExtensions(Revit.Elements)

#############################################



status	= []
test 	= []
doc		= DocumentManager.Instance.CurrentDBDocument
uiapp 	= DocumentManager.Instance.CurrentUIApplication



################### SEARCH FAMILY TYPE TO INSERT ######################

fec = FilteredElementCollector(doc).OfClass(FamilySymbol)

for i in fec:
	n1 = Element.Name.__get__(i)
	if n1 == 'Generic_DV':
		type = i
		
################### SEARCH ALL ELEMENTS IN ACTIIVE DOC ######################
#type = UnwrapElement(IN[0])

collector = FilteredElementCollector(doc)

viewcoll = collector.OfCategory(BuiltInCategory.OST_StructuralStiffener).WhereElementIsNotElementType().ToElements()

if len(viewcoll) > 0:
	TransactionManager.Instance.EnsureInTransaction(doc)
	for e in viewcoll:
		try:
			del_id = doc.Delete(e.Id) # delete
			status.append('deleted'+ str(e))
		except:
			status.append('failed')
	TransactionManager.Instance.TransactionTaskDone()
else:
	status.append('No SOP to be Deleted Continue..')

######################## ALL LINKED FILES ##############################

collector = FilteredElementCollector(doc)
linkInstances = collector.OfClass(Autodesk.Revit.DB.RevitLinkInstance)
linkDoc, linkName, linkPath = [], [], []

##########Find Instances in Linked Files################

app 			= uiapp.Application
uidoc 			= DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
list 			= []
pointlist 		= []
newLinks		= []
newLinksName	= []
CS 				= []
newCS 			= []
families 		= []
errors 			= []
ST = StructuralType.NonStructural
cs2 = CoordinateSystem.ByOrigin(0,0,0)

collectorB = FilteredElementCollector(doc)
BasePoint = collectorB.OfCategory(BuiltInCategory.OST_ProjectBasePoint).WhereElementIsNotElementType().ToElements()


EW 		= BasePoint[0].get_Parameter("E/W").AsDouble()*0.3048
NS		= BasePoint[0].get_Parameter("N/S").AsDouble()*0.3048
elev 	= BasePoint[0].get_Parameter("Elev").AsDouble()
Angle 	= BasePoint[0].get_Parameter("Angle to True North").AsDouble()
Angle  	= 360 - math.degrees(Angle)

World = CoordinateSystem.ByOrigin(EW,NS,elev)
Worigin = Point.ByCoordinates(EW,NS,elev)
Z = Vector.ByCoordinates(0,0,1)
Wplane = Plane.ByOriginNormal(Worigin,Z)

NewWorld = World.Rotate(Wplane,Angle)

BP = Worigin

for i,link in enumerate(linkInstances):

	Doc = link.GetLinkDocument()
	
	point		= []
	newPoints 	= []
	groups 		= []
	
	try:
		collector = FilteredElementCollector(Doc)
		BuiltIn = System.Enum.ToObject(BuiltInCategory, BuiltInCategory.OST_StructuralStiffener)
		filter 	= ElementCategoryFilter(BuiltIn)
		
		foundElement = collector.WherePasses(filter).WhereElementIsNotElementType().ToElements()
		
		if foundElement:
			list.append(foundElement)
			
			newLinks.append(Doc)
			Name = str(link.Name)
			Name = Name.split(' : ')[1]
			newLinksName.append(Name)
						
			tf1 = link.GetTransform()  
			
			cs1 = CoordinateSystem.ByOriginVectors(tf1.Origin.ToPoint(True),tf1.BasisX.ToVector(True), tf1.BasisY.ToVector(True), tf1.BasisZ.ToVector(True))			
			
			CS.append(cs1)
			
			
			for i,e in enumerate(foundElement):
				loc = e.Location.Point.ToPoint()
				point.append(loc)
				
				try:
					TransactionManager.Instance.EnsureInTransaction(doc)
			
					for p in e.Parameters:
						if p.Definition.Name == 'SOB Type':
							parm = p.AsValueString()
							if (parm is None):
								parm = p.AsString()
			
					#SOP = e.get_Parameter("SOP Type").AsValueString()
					#SOP = Element.GetParameterValueByName(e,"SOB type")
					errors.append('found paramenter is {}'.format(parm))
					
					TransactionManager.Instance.TransactionTaskDone()	
					
				except:
					errors.append('error here')
				
				try:		
					cs3 = Geometry.Transform(loc,cs2,cs1)
					newPoints.append(cs3)	
					
				except:				
					newPoints.append('No translation')		
				
				try:
					if len(Name) < 7:
						TransactionManager.Instance.EnsureInTransaction(doc)
						
						x = cs3.ToXyz()[0]
						y = cs3.ToXyz()[1]
						
						pt = Geometry.Transform(cs3,NewWorld)
						x = pt.ToXyz()[0]
						y = pt.ToXyz()[1]			

						fam = doc.Create.NewFamilyInstance(cs3.ToXyz(),type,ST)
						fam.get_Parameter("Name").Set(Name);
						fam.get_Parameter("Foundation X").Set(x);
						fam.get_Parameter("Foundation Y").Set(y);
						fam.get_Parameter("Foundation Type").Set(parm);
						fam.get_Parameter("SOB Type").Set(parm);
						groups.append(fam)

						TransactionManager.Instance.TransactionTaskDone()						
						
					else:
						groups.append('Family {} not Created {}'.format(Name,len(Name)))
				except: 
					groups.append('error')
					
				
				
		else:
			continue
			
		pointlist.append(point)
		newCS.append(newPoints)
		families.append(groups)
	except:	
		error = 'No Link'
	
if len(list) == len(families):
	OUT = 'Success: {} SOP Families Created'.format(len(families))
else: 
	OUT = 'Something Went Wrong'

#OUT = errors, list , pointlist , newLinksName , newLinks , CS , newCS, families , BP
#OUT = status , linkDoc , linkInstances
