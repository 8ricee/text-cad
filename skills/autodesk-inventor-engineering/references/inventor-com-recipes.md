# Autodesk Inventor PowerShell COM Recipes (`inventor_run_script`)

Use these patterns inside `inventor_run_script` (`$inv` and `$doc` are pre-bound).
Note: Inventor COM API internal length unit is **centimeters (`cm`)** (`10 mm = 1 cm`). Always write parameter expressions with `' mm'` suffix or divide `mm / 10.0`.

## 1. Create `UserParameters` on `MasterSkeleton.ipt` or Sheet Metal `.ipt`
```powershell
$cd = $doc.ComponentDefinition
$ups = $cd.Parameters.UserParameters
$ups.AddByExpression('PlateWidth', '740 mm', 11269) | Out-Null   # kMillimeterLengthUnits = 11269
$ups.AddByExpression('PlateHeight', '1140 mm', 11269) | Out-Null
$ups.AddByExpression('FlangeHeight', '20 mm', 11269) | Out-Null
```

## 2. Fully Constrained `PlanarSketch` + Sheet Metal `FaceFeature` & `FlangeFeature`
```powershell
$cd = $doc.ComponentDefinition
$sk = $cd.Sketches.Add($cd.WorkPlanes.Item(3)) # XY Plane
$p0 = $inv.TransientGeometry.CreatePoint2d(0, 0)
$p1 = $inv.TransientGeometry.CreatePoint2d(74.0, 114.0) # cm = 740 x 1140 mm
$rect = $sk.SketchLines.AddAsTwoPointRectangle($p0, $p1)
$sk.GeometricConstraints.AddGround($rect.Item(1).StartSketchPoint) | Out-Null
$dW = $sk.DimensionConstraints.AddTwoPointDistance($rect.Item(1).StartSketchPoint, $rect.Item(1).EndSketchPoint, 19201, $inv.TransientGeometry.CreatePoint2d(37, -5))
$dW.Parameter.Expression = 'PlateWidth'
$dH = $sk.DimensionConstraints.AddTwoPointDistance($rect.Item(2).StartSketchPoint, $rect.Item(2).EndSketchPoint, 19202, $inv.TransientGeometry.CreatePoint2d(79, 57))
$dH.Parameter.Expression = 'PlateHeight'
$prof = $sk.Profiles.AddForSolid()
$faceDef = $cd.Features.FaceFeatures.CreateFaceFeatureDefinition($prof)
$face = $cd.Features.FaceFeatures.Add($faceDef)
$doc.Update2($true)
```

## 3. Assembly Occurrence Placement & Grounding
```powershell
$asm = $doc.ComponentDefinition
$mat = $inv.TransientGeometry.CreateMatrix()
$occ = $asm.Occurrences.Add('C:\path\to\part.ipt', $mat)
$occ.Grounded = $true
```
