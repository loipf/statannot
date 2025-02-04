# from matplotlib.text import Text
import matplotlib.pyplot as plt
from matplotlib import lines
import matplotlib.transforms as mtransforms
from matplotlib.font_manager import FontProperties
import numpy as np
import pandas as pd
import seaborn as sns
from seaborn.utils import remove_na

from scipy import stats

DEFAULT = object()


def stat_test(box_data1, box_data2, test, **stats_params):
  test_short_name = ''
pval = None
formatted_output = None
if test == 'Levene':
  stat, pval = stats.levene(box_data1, box_data2, **stats_params)
test_short_name = 'levene'
formatted_output = ("Levene test of variance, "
                    "P_val={:.3e} stat={:.3e}").format(pval, stat)
elif test == 'Mann-Whitney':
  u_stat, pval = stats.mannwhitneyu(
    box_data1, box_data2, alternative='two-sided', **stats_params)
test_short_name = 'M.W.W.'
formatted_output = ("Mann-Whitney-Wilcoxon test two-sided "
                    "P_val={:.3e} U_stat={:.3e}").format(pval, u_stat)
elif test == 'Mann-Whitney-gt':
  u_stat, pval = stats.mannwhitneyu(
    box_data1, box_data2, alternative='greater', **stats_params)
test_short_name = 'M.W.W.'
formatted_output = ("Mann-Whitney-Wilcoxon test greater "
                    "P_val={:.3e} U_stat={:.3e}").format(pval, u_stat)
elif test == 'Mann-Whitney-ls':
  u_stat, pval = stats.mannwhitneyu(
    box_data1, box_data2, alternative='less', **stats_params)
test_short_name = 'M.W.W.'
formatted_output = ("Mann-Whitney-Wilcoxon test smaller "
                    "P_val={:.3e} U_stat={:.3e}").format(pval, u_stat)
elif test == 't-test_ind':
  stat, pval = stats.ttest_ind(a=box_data1, b=box_data2, **stats_params)
test_short_name = 't-test_ind'
formatted_output = ("t-test independent samples, "
                    "P_val={:.3e} stat={:.3e}").format(pval, stat)
elif test == 't-test_welch':
  stat, pval = stats.ttest_ind(
    a=box_data1, b=box_data2, equal_var=False, **stats_params)
test_short_name = 't-test_welch'
formatted_output = ("Welch's t-test independent samples, "
                    "P_val={:.3e} stat={:.3e}").format(pval, stat)
elif test == 't-test_paired':
  stat, pval = stats.ttest_rel(a=box_data1, b=box_data2, **stats_params)
test_short_name = 't-test_rel'
formatted_output = ("t-test paired samples, "
                    "P_val={:.3e} stat={:.3e}").format(pval, stat)
elif test == 'Wilcoxon':
  if "zero_method" in stats_params.keys():
  zero_method = stats_params["zero_method"]
del stats_params["zero_method"]
else:
  zero_method = len(box_data1) <= 20 and "pratt" or "wilcox"
print("Using zero_method ", zero_method)
stat, pval = stats.wilcoxon(
  box_data1, box_data2, zero_method=zero_method, **stats_params)
test_short_name = 'Wilcoxon'
formatted_output = ("Wilcoxon test (paired samples), "
                    "P_val={:.3e} stat={:.3e}").format(pval, stat)
return pval, formatted_output, test_short_name



def pvalAnnotation_text(x, pvalueThresholds):
  singleValue = False
if isinstance(x, np.array):
  x1 = x
else:
  x1 = np.array([x])
singleValue = True
# Sort the threshold array
pvalueThresholds = pd.DataFrame(pvalueThresholds).sort_values(by=0, ascending=False).values
xAnnot = pd.Series(["" for _ in range(len(x1))])
for i in range(0, len(pvalueThresholds)):
  if (i < len(pvalueThresholds) - 1):
  condition = (x1 <= pvalueThresholds[i][0]) & (pvalueThresholds[i + 1][0] < x1)
xAnnot[condition] = pvalueThresholds[i][1]
else:
  condition = x1 < pvalueThresholds[i][0]
xAnnot[condition] = pvalueThresholds[i][1]

return xAnnot if not singleValue else xAnnot.iloc[0]


def add_stat_annotation(ax,
                        data=None, x=None, y=None, hue=None, order=None, hue_order=None,
                        boxPairList=None,
                        test='Mann-Whitney', textFormat='star', loc='inside',
                        pvalueThresholds=[[1, "ns"], [0.05, "*"], [1e-2, "**"], [1e-3, "***"], [1e-4, "****"]],
                        useFixedOffset=False, lineYOffsetToBoxAxesCoord=None, lineYOffsetAxesCoord=None,
                        lineHeightAxesCoord=0.02, textYOffsetPoints=1,
                        color='0.2', linewidth=1.5, fontsize='medium', verbose=1, elevatedText=False):
  """
User should use the same argument for the data, x, y, hue, order, hue_order as the seaborn boxplot function.
boxPairList can be of either form:
For non-grouped boxplot: [(cat1, cat2), (cat3, cat4)]
For boxplot grouped by hue: [((cat1, hue1), (cat2, hue2)), ((cat3, hue3), (cat4, hue4))]
"""

def find_x_position_box(boxPlotter, boxName):
  """
boxName can be either a name "cat" or a tuple ("cat", "hue")
"""
if boxPlotter.plot_hues is None:
  cat = boxName
hueOffset = 0
else:
  cat = boxName[0]
hue = boxName[1]
hueOffset = boxPlotter.hue_offsets[boxPlotter.hue_names.index(hue)]

groupPos = boxPlotter.group_names.index(cat)
boxPos = groupPos + hueOffset
return boxPos

def get_box_data(boxPlotter, boxName):
  """
boxName can be either a name "cat" or a tuple ("cat", "hue")
Here we really have to duplicate seaborn code, because there is not direct access to the
box_data in the BoxPlotter class.
"""
if boxPlotter.plot_hues is None:
  cat = boxName
else:
  cat = boxName[0]
hue = boxName[1]

i = boxPlotter.group_names.index(cat)
group_data = boxPlotter.plot_data[i]

if boxPlotter.plot_hues is None:
  # Draw a single box or a set of boxes
  # with a single level of grouping
  box_data = remove_na(group_data)
else:
  hue_level = hue
hue_mask = boxPlotter.plot_hues[i] == hue_level
box_data = remove_na(group_data[hue_mask])

return box_data

fig = plt.gcf()

validList = ['inside', 'outside']
if loc not in validList:
  raise ValueError("loc value should be one of the following: {}.".format(', '.join(validList)))
validList = ['t-test_ind', 't-test_paired', 'Mann-Whitney']
if test not in validList:
  raise ValueError("test value should be one of the following: {}.".format(', '.join(validList)))

if verbose >= 1 and textFormat == 'star':
  print("pvalue annotation legend:")
pvalueThresholds = pd.DataFrame(pvalueThresholds).sort_values(by=0, ascending=False).values
for i in range(0, len(pvalueThresholds)):
  if (i < len(pvalueThresholds) - 1):
  print('{}: {:.2e} < p <= {:.2e}'.format(pvalueThresholds[i][1], pvalueThresholds[i + 1][0],
                                          pvalueThresholds[i][0]))
else:
  print('{}: p <= {:.2e}'.format(pvalueThresholds[i][1], pvalueThresholds[i][0]))
print()

# Create the same BoxPlotter object as seaborn's boxplot
boxPlotter = sns.categorical._BoxPlotter(x, y, hue, data, order, hue_order,
                                         orient=None, width=.8, color=None, palette=None, saturation=.75,
                                         dodge=True, fliersize=5, linewidth=None)
plotData = boxPlotter.plot_data

xtickslabels = [t.get_text() for t in ax.xaxis.get_ticklabels()]
ylim = ax.get_ylim()
yRange = ylim[1] - ylim[0]

if lineYOffsetAxesCoord is None:
  if loc == 'inside':
  lineYOffsetAxesCoord = 0.05
if lineYOffsetToBoxAxesCoord is None:
  lineYOffsetToBoxAxesCoord = 0.06
elif loc == 'outside':
  lineYOffsetAxesCoord = 0.03
lineYOffsetToBoxAxesCoord = lineYOffsetAxesCoord
else:
  if loc == 'inside':
  if lineYOffsetToBoxAxesCoord is None:
  lineYOffsetToBoxAxesCoord = 0.06
elif loc == 'outside':
  lineYOffsetToBoxAxesCoord = lineYOffsetAxesCoord

yOffset = lineYOffsetAxesCoord * yRange
yOffsetToBox = lineYOffsetToBoxAxesCoord * yRange

yStack = []
annList = []
for box1, box2 in boxPairList:
  
  valid = None
groupNames = boxPlotter.group_names
hueNames = boxPlotter.hue_names
if boxPlotter.plot_hues is None:
  cat1 = box1
cat2 = box2
hue1 = None
hue2 = None
label1 = '{}'.format(cat1)
label2 = '{}'.format(cat2)
valid = cat1 in groupNames and cat2 in groupNames
else:
  cat1 = box1[0]
hue1 = box1[1]
cat2 = box2[0]
hue2 = box2[1]
label1 = '{}_{}'.format(cat1, hue1)
label2 = '{}_{}'.format(cat2, hue2)
valid = cat1 in groupNames and cat2 in groupNames and hue1 in hueNames and hue2 in hueNames

if valid:
  # Get position of boxes
  x1 = find_x_position_box(boxPlotter, box1)
x2 = find_x_position_box(boxPlotter, box2)
box_data1 = get_box_data(boxPlotter, box1)
box_data2 = get_box_data(boxPlotter, box2)
ymax1 = box_data1.max()
ymax2 = box_data2.max()

pval, formattedOutput, testShortName = stat_test(box_data1, box_data2, test)
if verbose >= 2:
  print("{} v.s. {}: {}".format(label1, label2, formattedOutput))

if textFormat == 'full':
  text = "{} p < {:.2e}".format(testShortName, pval)
elif textFormat is None:
  text = None
elif textFormat == 'star':
  text = pvalAnnotation_text(pval, pvalueThresholds)

if loc == 'inside':
  yRef = max(ymax1, ymax2)
elif loc == 'outside':
  yRef = ylim[1]


### loipf edited version for boxes next to each other, not above
if elevatedText:
  if yStack:
  yRef2 = max(yRef, max(yStack))
else:
  yRef2 = yRef
else:
  yRef2 = yRef



if yStack:
  y = yRef2 + yOffsetToBox
else:
  y = yRef2 + yOffset
h = lineHeightAxesCoord * yRange
lineX, lineY = [x1, x1, x2, x2], [y, y + h, y + h, y]

if text != '':  ### loipf edited, dont plot ns values
  if loc == 'inside':
  ax.plot(lineX, lineY, lw=linewidth, c=color)
elif loc == 'outside':
  line = lines.Line2D(lineX, lineY, lw=linewidth, c=color, transform=ax.transData)
line.set_clip_on(False)
ax.add_line(line)

if text is not None:
  ann = ax.annotate(text, xy=(np.mean([x1, x2]), y + h),
                    xytext=(0, textYOffsetPoints), textcoords='offset points',
                    xycoords='data', ha='center', va='bottom', fontsize=fontsize,
                    clip_on=False, annotation_clip=False, color='red')
annList.append(ann)


ax.set_ylim((ylim[0], 1.1 * (y + h)))

if text is not None:
  plt.draw()
yTopAnnot = None
gotMatplotlibError = False
if not useFixedOffset:
  try:
  bbox = ann.get_window_extent()
bbox_data = bbox.transformed(ax.transData.inverted())
yTopAnnot = bbox_data.ymax
except RuntimeError:
  gotMatplotlibError = True

if useFixedOffset or gotMatplotlibError:
  if verbose >= 1:
  print(
    "Warning: cannot get the text bounding box. Falling back to a fixed y offset. Layout may be not optimal.")
# We will apply a fixed offset in points, based on the font size of the annotation.
fontsizePoints = FontProperties(size='medium').get_size_in_points()
offsetTrans = mtransforms.offset_copy(ax.transData, fig=fig,
                                      x=0, y=1.0 * fontsizePoints + textYOffsetPoints,
                                      units='points')
yTopDisplay = offsetTrans.transform((0, y + h))
yTopAnnot = ax.transData.inverted().transform(yTopDisplay)[1]
else:
  yTopAnnot = y + h

yStack.append(yTopAnnot)
else:
  raise ValueError("boxPairList contains an unvalid box pair.")

yStackMax = max(yStack)

if loc == 'inside':
  # ax.set_ylim((ylim[0], 1.03 * yStackMax))
  ax.set_ylim((ylim[0], max(ylim[1], 1.03 * yStackMax)) ) ### loipf edited
elif loc == 'outside':
  ax.set_ylim((ylim[0], ylim[1]))

return ax
