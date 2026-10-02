import cadquery as cq

# Main envelope, including the four diagonal 149 mm workholding flats.
result = cq.Workplane('XY').circle(75).extrude(24).intersect(cq.Workplane('XY').rect(149,149).extrude(24).rotate((0,0,0),(0,0,1),45))
rim = cq.Workplane('XY').workplane(offset=24).circle(75).workplane(offset=1).circle(74).loft(ruled=True)
flat_bevel = cq.Workplane('XY').workplane(offset=24).rect(149,149).workplane(offset=1).rect(147,147).loft(ruled=True).rotate((0,0,0),(0,0,1),45)
result = result.union(rim.intersect(flat_bevel))

# Main bore and its 1 x 45 degree upper chamfer.
result = result.cut(cq.Workplane('XY').circle(47.5).extrude(25))
bore_bevel = cq.Workplane('XY').workplane(offset=24).circle(47.5).workplane(offset=1).circle(48.5).loft(ruled=True)
result = result.cut(bore_bevel)

# Four 5 mm wide internal keys, ending at radius 42 and Z=13.
for a in (0,90,180,270):
    tab = cq.Workplane('XY').workplane(offset=13).center(0,-47.5).rect(5,11).extrude(11)
    tab_top = cq.Workplane('XY').workplane(offset=24).center(0,-47.5).rect(5,11).workplane(offset=1).center(0,-0.5).rect(3,10).loft(ruled=True)
    result = result.union(tab.union(tab_top).rotate((0,0,0),(0,0,1),a))

# R2.5 reliefs beside the keys, 12 mm deep, with upper chamfers.
for a in (0,90,180,270):
    relief = cq.Workplane('XY').workplane(offset=13).pushPoints([(-5,-47.5),(5,-47.5)]).circle(2.5).extrude(12)
    bridges = cq.Workplane('XY').workplane(offset=13).pushPoints([(-5,-44.75),(5,-44.75)]).rect(5,5.5).extrude(12)
    relief = relief.union(bridges)
    for x in (-5,5):
        relief_top = cq.Workplane('XY').workplane(offset=24).center(x,-47.5).circle(2.5).workplane(offset=1).circle(3.5).loft(ruled=True)
        bridge_top = cq.Workplane('XY').workplane(offset=24).center(x,-44.75).rect(5,5.5).workplane(offset=1).center(0,0.5).rect(7,6.5).loft(ruled=True)
        relief = relief.union(relief_top).union(bridge_top)
    result = result.cut(relief.rotate((0,0,0),(0,0,1),a))

# Outer pocket floor-edge chamfer: 0.25 x 45 degrees.
floor_bevel = cq.Workplane('XZ').polyline([(74.75,13),(75,12.75),(76,12.75),(76,13)]).close().revolve(360,(0,0),(0,1))

# Eight open peripheral pockets. The two master corner centers are
# (+/-23,-62.5), with R5 corners and 40/100 degree wall geometry.
for s in (1,-1):
    pocket = cq.Workplane('XY').workplane(offset=13).moveTo(s*-6.5417266028,-89.9278396763).lineTo(s*19.1697777844,-59.2860619516).threePointArc((s*23,-57.5),(s*25.5,-58.1698729811)).lineTo(s*60.1410161514,-78.1698729811).lineTo(s*65,-105).lineTo(s*-12,-105).close().extrude(13)
    pocket = pocket.edges('<Z').fillet(0.5)
    bevel = cq.Workplane('XY').workplane(offset=24.5).moveTo(s*-6.5417266028,-89.9278396763).lineTo(s*19.1697777844,-59.2860619516).threePointArc((s*23,-57.5),(s*25.5,-58.1698729811)).lineTo(s*60.1410161514,-78.1698729811).lineTo(s*65,-105).lineTo(s*-12,-105).close().workplane(offset=0.5).moveTo(s*-6.9247488244,-89.6064458714).lineTo(s*18.7867555628,-58.9646681467).threePointArc((s*23,-57),(s*25.75,-57.7368602792)).lineTo(s*60.3910161514,-77.7368602792).lineTo(s*65,-105).lineTo(s*-12,-105).close().loft(ruled=True)
    pocket = pocket.union(bevel)
    lip = floor_bevel.intersect(pocket.translate((0,0,-0.25)))
    for a in (0,90,180,270):
        result = result.cut(pocket.rotate((0,0,0),(0,0,1),a))
        result = result.cut(lip.rotate((0,0,0),(0,0,1),a))

# Four cardinal diameter-10 through holes on the inferred diameter-134 circle.
result = result.cut(cq.Workplane('XY').pushPoints([(67,0),(0,67),(-67,0),(0,-67)]).circle(5).extrude(25))

# Four diameter-9 through holes, diameter-15 counterbores 8.6 mm deep.
# Angular positions: 34, 124, 214 and 304 degrees.
result = result.cut(cq.Workplane('XY').pushPoints([(55.5455173664,37.4659245327),(-37.4659245327,55.5455173664),(-55.5455173664,-37.4659245327),(37.4659245327,-55.5455173664)]).circle(4.5).extrude(25))
result = result.cut(cq.Workplane('XY').workplane(offset=16.4).pushPoints([(55.5455173664,37.4659245327),(-37.4659245327,55.5455173664),(-55.5455173664,-37.4659245327),(37.4659245327,-55.5455173664)]).circle(7.5).extrude(8.6))

# Eight diameter-5 blind holes, 12 mm deep, paired at 10 degrees.
result = result.cut(cq.Workplane('XY').workplane(offset=13).pushPoints([(36.7695526217,36.7695526217),(29.8259746903,42.5959063030),(-36.7695526217,36.7695526217),(-42.5959063030,29.8259746903),(-36.7695526217,-36.7695526217),(-29.8259746903,-42.5959063030),(36.7695526217,-36.7695526217),(42.5959063030,-29.8259746903)]).circle(2.5).extrude(12))
result = result.clean()
