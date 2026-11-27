# Autodesk Inventor In-Process iLogic VB.NET Recipes (`inventor_run_script`)

Use these patterns inside `inventor_run_script` (`ilogic_script`).
`Agy.InventorBridge` executes the rule **in-process on Inventor's STA UI thread** wrapped in an **atomic `Inventor.Transaction`** (`txn.Abort()` rolls back every sketch, feature, parameter, and constraint on error).
`ThisApplication` (`Inventor.Application`) and `ThisDoc.Document` (`Inventor.Document`) are pre-bound natively.
Note: Inventor API internal length unit is **centimeters (`cm`)** (`10 mm = 1 cm`). Always write parameter expressions with `" mm"` suffix or divide `mm / 10.0`.

## 1. Create `UserParameters` on `MasterSkeleton.ipt` or Sheet Metal `.ipt`
```vbnet
Dim doc As PartDocument = CType(ThisDoc.Document, PartDocument)
Dim ups As UserParameters = doc.ComponentDefinition.Parameters.UserParameters
ups.AddByExpression("PlateWidth", "740 mm", UnitsTypeEnum.kMillimeterLengthUnits)
ups.AddByExpression("PlateHeight", "1140 mm", UnitsTypeEnum.kMillimeterLengthUnits)
ups.AddByExpression("FlangeHeight", "20 mm", UnitsTypeEnum.kMillimeterLengthUnits)
```

## 2. Fully Constrained `PlanarSketch` + Sheet Metal `FaceFeature` & `FlangeFeature`
```vbnet
Dim doc As PartDocument = CType(ThisDoc.Document, PartDocument)
Dim cd As SheetMetalComponentDefinition = CType(doc.ComponentDefinition, SheetMetalComponentDefinition)
Dim tg As TransientGeometry = ThisApplication.TransientGeometry

Dim sk As PlanarSketch = cd.Sketches.Add(cd.WorkPlanes.Item(3)) ' XY Plane
Dim rect As SketchEntitiesEnumerator = sk.SketchLines.AddAsTwoPointRectangle(
    tg.CreatePoint2d(0, 0),
    tg.CreatePoint2d(74.0, 114.0)) ' cm = 740 x 1140 mm

Dim l1 As SketchLine = CType(rect.Item(1), SketchLine)
Dim l2 As SketchLine = CType(rect.Item(2), SketchLine)
sk.GeometricConstraints.AddGround(l1.StartSketchPoint)

Dim dW = sk.DimensionConstraints.AddTwoPointDistance(
    l1.StartSketchPoint, l1.EndSketchPoint,
    DimensionOrientationEnum.kHorizontalDim, tg.CreatePoint2d(37, -5))
dW.Parameter.Expression = "PlateWidth"

Dim dH = sk.DimensionConstraints.AddTwoPointDistance(
    l2.StartSketchPoint, l2.EndSketchPoint,
    DimensionOrientationEnum.kVerticalDim, tg.CreatePoint2d(79, 57))
dH.Parameter.Expression = "PlateHeight"

Dim prof As Profile = sk.Profiles.AddForSolid()
Dim faceDef As FaceFeatureDefinition = cd.Features.FaceFeatures.CreateFaceFeatureDefinition(prof)
cd.Features.FaceFeatures.Add(faceDef)
```

## 3. Assembly Occurrence Placement & Grounding
```vbnet
Dim asmDoc As AssemblyDocument = CType(ThisDoc.Document, AssemblyDocument)
Dim mat As Matrix = ThisApplication.TransientGeometry.CreateMatrix()
Dim occ As ComponentOccurrence = asmDoc.ComponentDefinition.Occurrences.Add("C:\path\to\part.ipt", mat)
occ.Grounded = True
```
