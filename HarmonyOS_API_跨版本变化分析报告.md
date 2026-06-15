# HarmonyOS API 跨版本迁移变化分析报告

> 基于知识图谱分析，覆盖 API4.1、API5.0、API5.1、API6.0 四个版本

## 一、版本数据总览

| 版本 | 总节点数 | 类/接口/枚举 | 方法/属性 | 模块数 |
|------|----------|-------------|----------|--------|
| API4.1 | 6,197 | 434 / 206 | 2181 / 1033 | 310 |
| API5.0 | 15,335 | 1762 / 543 | 4770 / 3974 | 71 |
| API5.1 | 16,468 | 1887 / 570 | 5001 / 4363 | 71 |
| API6.0 | 16,570 | 1906 / 557 | 5109 / 4547 | 72 |

## 二、4.1 → 5.0（大爆炸——框架创立期）

### 2.1 总览

| 维度 | 新增 | 删除 | 净变化 |
|------|------|------|--------|
| 类/接口/枚举 | +1729 | -64 | +1665 |
| 方法/属性 | +5917 | -387 | +5530 |

### 2.2 新增类/接口/枚举（按模块）

#### @kit.ArkUI (+1255：Class 350 / Interface 640 / Enum 265)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | AbilityComponentAttribute | Define the attribute functions of ability component. |
| Class | AlertDialog | Defines AlertDialog which uses show method to show alert dialog. |
| Class | AlphabetIndexerAttribute | Defines the alphabet index bar attribute functions. |
| Class | AlphabetIndexerModifier | Defines AlphabetIndexer Modifier |
| Class | AnimatedDrawableDescriptor | Define the data structure for PixelMap animations. |
| Class | AnimatorAttribute | Defines AnimatorAttribute. |
| Class | AppStorage | AppStorage singleton is sub-class of see LocalStorage for UI state of app-wide a |
| Class | AppStorageV2 | AppStorageV2 is for UI state of app-wide access, has same life cycle as the app, |
| Class | AppearSymbolEffect | Defines AppearSymbolEffect class. |
| Class | AttributeUpdater | Defines a modifier which can update attributes to native side. |
| Class | BackgroundColorStyle | Defines Sets the property string background color. |
| Class | BadgeAttribute | Defines Badge Component attribute. |
| Class | BaseShape | Base shape class |
| Class | BaseSpan | Define the BaseSpan class, contains the common methods of span. |
| Class | BaselineOffsetStyle | Defines BaselineOffsetStyle. |
| Class | BasicPrefetcher | Basic implementation of {@link IPrefetcher}. It provides an intelligent data pre |
| Class | BlankAttribute | Inheritance CommonMethod Set Styles |
| Class | BlankModifier | Defines Blank Modifier |
| Class | BottomTabBarStyle | Define BottomTabBarStyle, the style is icon and text. |
| Class | BounceSymbolEffect | Defines BounceSymbolEffect class. |
| Class | BuilderNode | Defines BuilderNode. |
| Class | ButtonAttribute | Defines the button attribute functions. |
| Class | ButtonModifier | Defines Button Modifier |
| Class | CalendarAttribute |  |
| Class | CalendarController | Calendar controller. |
| Class | CalendarPickerAttribute | Defines the CalendarPicker attribute functions. |
| Class | CalendarPickerDialog | Defines CalendarPickerDialog which uses show method to show CalendarPicker dialo |
| Class | CalendarPickerModifier | Defines CalendarPicker Modifier |
| Class | CanvasAttribute | Provides attribute for Canvas. |
| Class | CanvasGradient | Opaque objects that describe gradients, created by createLinearGradient() or cre |
| Class | CanvasPath | Path object, which provides basic methods for drawing paths. |
| Class | CanvasRenderer | Canvas renderer for drawing shapes, text, images and other objects |
| Class | CanvasRenderingContext2D | Draw context object for the Canvas component. |
| Class | CheckboxAttribute | Defines the attribute functions of Checkbox. |
| Class | CheckboxGroupAttribute | Defines the attribute functions of CheckboxGroup. |
| Class | CheckboxGroupModifier | Defines CheckboxGroup Modifier |
| Class | CheckboxModifier | Defines Checkbox Modifier |
| Class | ChildrenMainSize | Indicates children main size. |
| Class | CircleAttribute | Circle drawing component attribute functions. |
| Class | CircleShape | Defines a circle drawing class. |
| Class | ColorContent | Defines the ColorContent. |
| Class | ColorFilter | Defines the ColorFilter object. |
| Class | ColorMetrics | Defines the ColorMetrics class. |
| Class | ColumnAttribute | Defines the Column component attribute functions. |
| Class | ColumnModifier | Defines Column Modifier |
| Class | ColumnSplitAttribute | Defines the ColumnSplit component attribute functions. |
| Class | ColumnSplitModifier | Defines ColumnSplit Modifier |
| Class | CommonAttribute | CommonAttribute for ide. |
| Class | CommonMethod | CommonMethod. |
| Class | CommonModifier | Defines Common Modifier |
| Class | CommonShapeMethod | Common shape method class |
| Class | CommonTransition | Provides interfaces for common transitions. |
| Class | Component3DAttribute |  |
| Class | ComponentContent | Defines ComponentContent. |
| Class | ComponentSnapshot | class ComponentSnapshot |
| Class | ContainerSpanAttribute | Define the ContainerSpan attribute functions. |
| Class | ContainerSpanModifier | Defines ContainerSpan modifier, the base class for quick use modifier ability |
| Class | Content | Defines the base class for ComponentContent and NodeContent. |
| Class | ContentSlotAttribute | Define ContentSlot attribute, to prevent improper recursive usage of ContentSlot |
| Class | ContextMenu | Defines Close contextMenu. |
| Class | ContextMenuController | class ContextMenuController |
| Class | CounterAttribute | Defines the Counter attribute functions. |
| Class | CounterModifier | Defines Counter Modifier |
| Class | CursorController | class CursorController |
| Class | CustomComponent | Custom Component |
| Class | CustomDialogController | Use the CustomDialogController class to display the custom pop-up window. |
| Class | CustomSpan | Defines CustomSpan. |
| Class | DataPanelAttribute | Defines the DataPanel attribute functions. |
| Class | DataPanelModifier | Defines DataPanel Modifier |
| Class | DatePickerAttribute | Defines the DatePicker attribute functions. |
| Class | DatePickerDialog | Defines DatePickerDialog which uses show method to show DatePicker dialog. |
| Class | DatePickerModifier | Defines DatePicker Modifier |
| Class | DecorationStyle | Defines DecorationStyle. |
| Class | DigitIndicator | Define DigitIndicator, the indicator type is digit. |
| Class | DisappearSymbolEffect | Defines DisappearSymbolEffect class. |
| Class | DividerAttribute | Defines the Divider attribute functions. |
| Class | DividerModifier | Defines Divider Modifier |
| Class | DotIndicator | Define DotIndicator, the indicator type is dot. |
| Class | DrawContext | Defines DrawContext. |
| Class | DrawModifier | Defined the draw modifier of node. Provides draw callbacks for the associated No |
| Class | DrawingRenderingContext | Defines DrawingRenderingContext. |
| Class | DynamicNode | Define DynamicNode. |
| Class | DynamicSyncScene | Represents a dynamic synchronization scene. |
| Class | EffectComponentAttribute | Defines the Effect Component attribute functions. |
| Class | EllipseAttribute |  |
| Class | EllipseShape | Defines an ellipse drawing class. |
| Class | EmbeddedComponentAttribute | Define the attribute functions of EmbeddedComponent. |
| Class | Environment | Defines the Environment interface. |
| Class | EventTargetInfo | Defines the event target information. |
| Class | FeatureAbility |  |
| Class | FlexAttribute | Defines the Flex attribute functions. |
| Class | FlowItemAttribute | Defines the water flow item attribute. |
| Class | FocusController | class FocusController |
| Class | FolderStackAttribute |  |
| Class | ForEachAttribute | declare ForEachAttribute |
| Class | FormComponentAttribute |  |
| Class | FormComponentModifier | Defines FormComponent Modifier |
| Class | FormLinkAttribute | Defines the FormLink attribute. |
| Class | FrameCallback | Class FrameCallback |
| Class | FrameNode | Defines FrameNode. |
| Class | FrictionMotion | Friction animation model. You can build friction animation by friction force, in |
| Class | GaugeAttribute |  |
| Class | GaugeModifier | Defines Gauge Modifier |
| Class | GestureGroupHandler | Defines the GestureGroup handler. |
| Class | GestureHandler | Defines the gesture handler. |
| Class | GestureRecognizer | Defines the gesture recognizer. |
| Class | GestureStyle | Defines GestureStyle. |
| Class | GridAttribute | Defines the grid attribute functions. |
| Class | GridColAttribute | Defines the GridContainer attribute functions. |
| Class | GridColModifier | Defines GridCol Modifier |
| Class | GridContainerAttribute | Defines the grid container attribute from inheritance Column |
| Class | GridItemAttribute |  |
| Class | GridItemModifier | Defines GridItem Modifier |
| Class | GridModifier | Defines Grid Modifier |
| Class | GridRowAttribute | Defines the GridRow attribute functions. |
| Class | GridRowModifier | Defines GridRow Modifier |
| Class | HierarchicalSymbolEffect | Defines HierarchicalSymbolEffect class. |
| Class | HyperlinkAttribute | Defines the hyperlink attribute functions |
| Class | HyperlinkModifier | Defines Hyperlink Modifier |
| Class | Image | You can create an Image object by calling new Image(). |
| Class | ImageAnalyzerController | Image analyzer controller. |
| Class | ImageAnimatorAttribute | inheritance CommonMethod |
| Class | ImageAnimatorModifier | Defines ImageAnimator Modifier |
| Class | ImageAttachment | Defines ImageAttachment. |
| Class | ImageAttribute |  |
| Class | ImageBitmap | Defines the ImageBitmap. |
| Class | ImageData | An ImageData object is a common object that stores the actual pixel data of a Ca |
| Class | ImageModifier | Defines Image Modifier |
| Class | ImageSpanAttribute | Define the ImageSpan attribute functions. |
| Class | ImageSpanModifier | Defines ImageSpan Modifier |
| Class | Indicator | Defines the indicator class. |
| Class | IndicatorComponentAttribute | Defines the IndicatorComponent attribute functions. |
| Class | IndicatorComponentController | Provides methods for switching components. |
| Class | IsolatedComponentAttribute | Define the attribute functions of IsolatedComponent. |
| Class | LayoutPolicy | Defines the policy of Layout |
| Class | LazyForEachAttribute | declare ForEachAttribute |
| Class | LengthMetrics | Defines the Length Metrics. |
| Class | LetterSpacingStyle | Defines LetterSpacingStyle. |
| Class | LineAttribute | inheritance CommonShapeMethod. |
| Class | LineHeightStyle | Defines LineHeightStyle. |
| Class | LineModifier | Defines Line Modifier |
| Class | LinearGradient | LinearGradient class |
| Class | ListAttribute |  |
| Class | ListItemAttribute |  |
| Class | ListItemGroupAttribute | Defines the item group attribute functions. |
| Class | ListItemGroupModifier | Defines ListItemGroup Modifier |
| Class | ListItemModifier | Defines ListItem Modifier |
| Class | ListModifier | Defines List Modifier |
| Class | ListScroller |  |
| Class | LoadingProgressAttribute | Declare the progress bar being loaded |
| Class | LoadingProgressModifier | Defines LoadingProgress Modifier |
| Class | LocalStorage | LocalStorage Class implements a Map of ObservableObjectBase UI state variables.  |
| Class | Locate |  |
| Class | LocationButtonAttribute | Defines the attributes of the location button. |
| Class | LongPressGestureHandler | Defines the LongPressGesture handler. |
| Class | MarqueeAttribute | Declares marquee properties. |
| Class | MarqueeDynamicSyncScene | Represents a dynamic synchronization scene of Marquee. |
| Class | MarqueeModifier | Defines Marquee Modifier |
| Class | Matrix2D | 2D transformation matrix, supporting rotation, translation, and scaling of the X |
| Class | MeasureUtils | class MeasureUtils |
| Class | MediaCachedImageAttribute | Attributes of MediaCachedImage inherited from ImageAttribute. |
| Class | MenuAttribute | Defines the Menu component attribute functions. |
| Class | MenuItemAttribute | Defines the MenuItem component attribute functions. |
| Class | MenuItemGroupAttribute | Defines the MenuItemGroup component attribute functions. |
| Class | MenuItemModifier | Defines MenuItem Modifier |
| Class | MenuModifier | Defines Menu Modifier |
| Class | MutableStyledString | MutableStyledString |
| Class | NavDestinationAttribute | The attribute function of NavDestination |
| Class | NavDestinationModifier | Defines NavDestination Modifier |
| Class | NavPathInfo | Indicates the information of NavDestination. |
| Class | NavPathStack | Indicates the information of NavDestinations. Providers methods for controlling  |
| Class | NavRouterAttribute | The attribute function of NavRouter |
| Class | NavRouterModifier | Defines NavRouter Modifier |
| Class | NavigationAttribute | Declare Navigation view properties. |
| Class | NavigationModifier | Defines Navigation Modifier |
| Class | NavigatorAttribute | Declare navigator properties. |
| Class | NavigatorModifier | Defines Navigator Modifier |
| Class | NodeAdapter | Used for lazy loading of typeNode. |
| Class | NodeContainerAttribute | Defines the attribute of NodeContainer, extends from CommonMethod. |
| Class | NodeContent | NodeContent is the entity encapsulation of the node content. |
| Class | NodeController | Defined the controller of node container.Provides lifecycle callbacks for the as |
| Class | OffscreenCanvas | OffscreenCanvas provides a Canvas object that can be rendered off-screen. It wor |
| Class | OffscreenCanvasRenderingContext2D | Draw context object for the OffscreenCanvas component. |
| Class | OverlayManager | class OverlayManager |
| Class | PanGestureHandler | Defines the PanGesture handler. |
| Class | PanGestureOptions | Defines the PanGesture options. |
| Class | PanRecognizer | Defines the gesture recognizer. |
| Class | PanelAttribute | Pane Attribute. |
| Class | PanelModifier | Defines Panel Modifier |
| Class | ParagraphStyle | Defines ParagraphStyle. |
| Class | ParticleAttribute | Defines the Particle component attribute functions. |
| Class | ParticleModifier | Defines Panel Modifier |
| Class | PasteButtonAttribute | Defines the attributes of the paste button. |
| Class | Path2D | 2D path object for path drawing |
| Class | PathAttribute | Provides methods for attribute path component. |
| Class | PathModifier | Defines Path Modifier |
| Class | PathShape | Defines a path drawing class. |
| Class | PatternLockAttribute | Provides methods for attribute pattern lock component. |
| Class | PatternLockController | Provides methods for control pattern lock component. |
| Class | PatternLockModifier | Defines PatternLock Modifier |
| Class | PersistenceV2 | PersistenceV2 is for UI state of app-wide access, available on app re-start, and |
| Class | PersistentStorage | Defines the PersistentStorage interface. |
| Class | PinchGestureHandler | Defines the PinchGesture handler. |
| Class | PixelMapDrawableDescriptor | Use the PixelMapDrawableDescriptor class to get the resource of pixelmap or reso |
| Class | PluginComponentAttribute | Defines the plugin component attribute functions. |
| Class | PolygonAttribute | Provides attribute for Polygon. |
| Class | PolygonModifier | Defines Polygon Modifier |
| Class | PolylineAttribute |  |
| Class | PolylineModifier | Defines Polyline Modifier |
| Class | ProgressAttribute | Defines the progress attribute functions. |
| Class | ProgressMask | Defines the ProgressMask class. |
| Class | ProgressModifier | Defines Progress Modifier |
| Class | PulseSymbolEffect | Defines PulseSymbolEffect class. |
| Class | QRCodeAttribute | Defines the qrcode attribute functions. |
| Class | QRCodeModifier | Defines QRCode Modifier |
| Class | RadioAttribute | Provides methods for radio method component. |
| Class | RadioModifier | Defines Radio Modifier |
| Class | RatingAttribute | Defines the rating attribute functions. |
| Class | RatingModifier | Defines Rating Modifier |
| Class | RectAttribute | rect attribute declaration. |
| Class | RectModifier | Defines Rect Modifier |
| Class | RectShape | Defines a rect drawing class. |
| Class | RefreshAttribute | Defines the refresh attribute functions. |
| Class | RefreshModifier | Defines Refresh Modifier |
| Class | RelativeContainerAttribute |  |
| Class | RemoteWindowAttribute | Inheritance CommonMethod Set Styles |
| Class | RenderNode | Defines RenderNode. Contains node tree operations and render property operations |
| Class | RenderingContextSettings | This object allows you to set properties when creating a rendering context |
| Class | RepeatAttribute | Defines the Repeat component attribute functions. |
| Class | ReplaceSymbolEffect | Defines ReplaceSymbolEffect class. |
| Class | RichEditorAttribute | Provides attribute for RichEditor. |
| Class | RichEditorBaseController | Provides Base Controller for RichEditor. |
| Class | RichEditorController | Provides Controller for RichEditor. |
| Class | RichEditorModifier | Defines RichEditor Modifier |
| Class | RichEditorStyledStringController | Provides Controller for RichEditor with StyledString. |
| Class | RichTextAttribute | Defines the RichText attribute functions. |
| Class | RootSceneAttribute | Defines the attribute functions of RootScene. |
| Class | RotationGestureHandler | Defines the RotationGesture handler. |
| Class | RowAttribute | Defines the row attribute functions. |
| Class | RowModifier | Defines Row Modifier |
| Class | RowSplitAttribute |  |
| Class | RowSplitModifier | Defines RowSplit Modifier |
| Class | SaveButtonAttribute | Defines the attributes of the save button. |
| Class | ScaleSymbolEffect | Defines ScaleSymbolEffect class. |
| Class | ScreenAttribute | Defines the attribute functions of Screen. |
| Class | ScrollAttribute | Defines the scroll attribute functions. |
| Class | ScrollBarAttribute | Defines the scrollbar attribute functions. |
| Class | ScrollModifier | Defines Scroll Modifier |
| Class | ScrollMotion | Rolling animation model: You can build rolling animation based on the initial po |
| Class | ScrollResult | The actual offset by which the scrollable scrolls. |
| Class | ScrollableCommonMethod | CommonScrollableMethod |
| Class | ScrollableTargetInfo | Defines the scrollable target information. |
| Class | Scroller | Scroller |
| Class | SearchAttribute | The attribute function of search |
| Class | SearchController | Provides the method of switching the cursor position. |
| Class | SearchModifier | Defines Search Modifier |
| Class | SectionOptions | Defines the water flow section options. |
| Class | SecurityComponentMethod | Defines the method of a security component. |
| Class | SelectAttribute | The commonMethod of select. |
| Class | SelectModifier | Defines Select Modifier |
| Class | ShapeAttribute |  |
| Class | ShapeClip | Define ShapeClip. Record the type and parameters of the shape used for clipping. |
| Class | ShapeMask | Defines ShapeMask. |
| Class | ShapeModifier | Defines Shape Modifier |
| Class | SideBarContainerAttribute | The attribute function of sidebar |
| Class | SideBarContainerModifier | Defines SideBarContainer Modifier |
| Class | SliderAttribute | Defines the attribute functions of Slider. |
| Class | SliderModifier | Defines Slider Modifier |
| Class | SpanAttribute |  |
| Class | SpanModifier | Defines Span Modifier |
| Class | SpringMotion | Spring animation model. You can build a spring animation based on the start poin |
| Class | SpringProp | Customize spring properties. |
| Class | StackAttribute |  |
| Class | StackModifier | Defines Stack Modifier |
| Class | StepperAttribute | Defines the stepper attribute functions |
| Class | StepperItemAttribute | Defines the stepper item attribute functions. |
| Class | StepperItemModifier | Defines StepperItem Modifier |
| Class | Storage | Defines the base class of storage. |
| Class | StyledString | StyledString |
| Class | SubTabBarStyle | Define SubTabBarStyle, the style is text and underline. |
| Class | SubscribaleAbstract | Defines the Subscribale base class. |
| Class | SubscribedAbstractProperty | SubscribedAbstractProperty<T> is the return value of - AppStorage static functio |
| Class | SwipeGestureHandler | Defines the SwipeGesture handler. |
| Class | SwiperAttribute | Defines the swiper attribute functions. |
| Class | SwiperController | Provides methods for switching components. |
| Class | SwiperDynamicSyncScene | Represents a dynamic synchronization scene of Swiper. |
| Class | SwiperModifier | Defines Swiper Modifier |
| Class | SymbolEffect | Defines SymbolEffect class. |
| Class | SymbolGlyphAttribute | Provides attribute for SymbolGlyph. |
| Class | SymbolGlyphModifier | Defines SymbolGlyph Modifier |
| Class | SymbolSpanAttribute | Provides attribute for SymbolSpan. |
| Class | SymbolSpanModifier | Defines SymbolSpan Modifier. Provided for use by the SymbolSpan component |
| Class | SyncedPropertyTwoWay | Defines the state value. |
| Class | TabBarSymbol | TabBarSymbol object. |
| Class | TabContentAttribute | Defines the attribute functions of TabContent. |
| Class | TabsAttribute | Defines the tabs attribute functions. |
| Class | TabsController | Provides methods for switching tabs. |
| Class | TabsModifier | Defines Tabs Modifier |
| Class | TapGestureHandler | Defines the TapGesture handler. |
| Class | TextAreaAttribute | Defines the attribute functions of TextArea. |
| Class | TextAreaController | Provides the method of switching the cursor position. |
| Class | TextAreaModifier | Defines TextArea Modifier |
| Class | TextAttribute |  |
| Class | TextClockAttribute | Provides attribute for TextClock. |
| Class | TextClockController | Provides a way to control the textclock status. |
| Class | TextClockModifier | Defines TextClock Modifier |
| Class | TextContentControllerBase | TextContentControllerBase |
| Class | TextController | Defines the controller of Text. |
| Class | TextInputAttribute | Defines the TextInput attribute functions. |
| Class | TextInputController | Provides the method of switching the cursor position. |
| Class | TextInputModifier | Defines TextInput Modifier |
| Class | TextMenuItemId | Defines the TextMenuItemId. |
| Class | TextModifier | Defines Text Modifier |
| Class | TextPickerAttribute | Style the text selector. |
| Class | TextPickerDialog | Defines TextPickerDialog which uses show method to show TextPicker dialog. |
| Class | TextPickerModifier | Defines TextPicker Modifier |
| Class | TextShadowStyle | Defines TextShadowStyle. |
| Class | TextStyle | Defines TextStyle. |
| Class | TextTimerAttribute | Defines the TextTimer attribute functions. |
| Class | TextTimerController | Provides a way to control the process. |
| Class | TextTimerModifier | Defines TextTimer Modifier |
| Class | ThemeControl | Class ThemeControl provides the Theme management for whole Ability and pages. |
| Class | TimePickerAttribute | Defines the TimePicker attribute functions. |
| Class | TimePickerDialog | Defines TimePickerDialog which uses show method to show TimePicker dialog. |
| Class | TimePickerModifier | Defines TimePicker Modifier |
| Class | ToggleAttribute | Defines the toggle attribute functions |
| Class | ToggleModifier | Defines Toggle Modifier |
| Class | TouchResult | Defines TouchResult class. |
| Class | TouchTestInfo | Defines TouchTestInfo class. |
| Class | TransitionEffect | Defines the transition effect |
| Class | UIExtensionComponentAttribute | Define the attribute functions of UIExtensionComponent. |
| Class | UIUtils | UIUtils is a state management tool class for operating the observed data. |
| Class | UrlStyle | Defines the URLStyle hyperlink that allows setting a URL string. When clicking o |
| Class | UserDataSpan | Defines UserDataSpan. Used to store and obtain user data. |
| Class | VideoAttribute | Defines the video attribute functions. |
| Class | VideoController | Defines the video controller. |
| Class | VideoModifier | Defines Video Modifier |
| Class | View | View |
| Class | WaterFlowAttribute | Defines the water flow attribute. |
| Class | WaterFlowModifier | Defines WaterFlow Modifier |
| Class | WaterFlowSections | Indicates the sections of WaterFlow. |
| Class | WindowExtensionContext | The context of window extension. It allows access to windowExtension-specific re |
| Class | WindowSceneAttribute | Defines the attribute functions of WindowScene. |
| Class | WithThemeAttribute | Defines the WithTheme attribute functions.. |
| Class | WrappedBuilder | Defines the WrappedBuilder class. |
| Class | XComponentAttribute | Defines XComponentAttribute. |
| Class | XComponentController | Defines XComponentController |
| Class | XComponentNode | Defines XComponent Node. |
| Class | console | Provide console |
| Class | dom | global dom |
| Enum | AccessibilityHoverType | Type of accessibility hover event. |
| Enum | AdaptiveColor | Defines adaptive color |
| Enum | Alignment | Alignment enumeration description. |
| Enum | AnimationMode | Declare the animation mode of tab content. |
| Enum | AnimationStatus | Animation status. |
| Enum | AppRotation | Enumerates the app rotation. |
| Enum | ArrowPointPosition | ArrowPointPosition enumeration description |
| Enum | ArrowPosition | The enum for arrow position in the select |
| Enum | Axis | Axis enumeration description. |
| Enum | AxisModel | Type of axis. |
| Enum | BadgePosition | Defines the badge position property. |
| Enum | BarMode | Declare the graphic format of the bar chart. |
| Enum | BarPosition | Declare the location of the bar chart. |
| Enum | BarState | Used to set the status of the scroll bar. |
| Enum | BarStyle | Declare BarStyle enum. |
| Enum | BarrierDirection | Specifies the direction value of Barrier. |
| Enum | BlendApplyType | Enum for BlendApplyType. Indicate how to apply specified blend mode to the view' |
| Enum | BlendMode | Enum for BlendMode. Blend modes for compositing current component with overlappi |
| Enum | BlurStyle | enum Blur style |
| Enum | BlurStyleActivePolicy | Enumerates the policies for activating the blur style. |
| Enum | BorderStyle | Border Style |
| Enum | BreakpointsReference | Defines the breakpoint reference of grid-container component. |
| Enum | ButtonRole | Enum for button role. |
| Enum | ButtonStyleMode | Enum for button style type. |
| Enum | ButtonType | Provides a button component. |
| Enum | CalendarAlign | The type of alignment between entry and calendar. |
| Enum | CancelButtonStyle | Enum for the style of cancel button |
| Enum | ChainEdgeEffect | Declare edge effect of chain animation. |
| Enum | ChainStyle | Defines the style of the chain in relative container. |
| Enum | CheckBoxShape | common enum of the checkbox shape |
| Enum | ClickEffectLevel | Enum of click effect level. |
| Enum | Color | common enum of color |
| Enum | ColorMode | Defines the ColorMode of device. |
| Enum | ColoringStrategy | Common enum of color strategy |
| Enum | ContentClipMode | Enum of scrollable containers' content clip mode. |
| Enum | ContentType | Declare the type of input content |
| Enum | ControlSize | Enum for Control Size. |
| Enum | CopyOptions | Indicates the share option. |
| Enum | Curve | Sets the animation playback mode. By default, the animation starts to play again |
| Enum | DataOperationType | Defines type to operation data source. |
| Enum | DataPanelType | DataPanelType enum |
| Enum | DialogAlignment | The alignment of dialog, |
| Enum | DialogButtonDirection | The arrangement of buttons in dialog. |
| Enum | DialogButtonStyle | The Button Style of dialog, |
| Enum | Direction | Sets the horizontal layout of elements. |
| Enum | DismissReason | Dismiss reason type. |
| Enum | DistributionType | Enumerates the color distribution types of a particle. |
| Enum | DisturbanceFieldShape | Defines particle disturbance shape. |
| Enum | DpiFollowStrategy | Enumeration of different types of DpiFollowStrategy. |
| Enum | DragBehavior | Enum for Drag Behavior. |
| Enum | DragPreviewMode | Defines the drag preview mode. |
| Enum | DragResult | Enum for Drag Result. |
| Enum | DynamicRangeMode |  |
| Enum | Edge | Edge. |
| Enum | EdgeEffect | Sliding effect |
| Enum | EditMode | Declare whether the ListItem element is editable. |
| Enum | EffectDirection | The direction type of symbol effect |
| Enum | EffectFillStyle | Declare fill style of symbol |
| Enum | EffectScope | Declare scope type of the symbol effect |
| Enum | EffectType | Enum of using the effects template mode. |
| Enum | EllipsisMode | Enum of ellipsisMode |
| Enum | EmbeddedType | Enum of EmbeddedType |
| Enum | EnterKeyType | Declare the type of soft keyboard. |
| Enum | ExpandMode | Enum for the expand mode. |
| Enum | FillMode | Sets the state before and after the animation starts. |
| Enum | FinishCallbackType | Enum for FinishCallbackType. |
| Enum | FlexAlign | FlexAlign enumeration description. |
| Enum | FlexDirection | FlexDirection enumeration description |
| Enum | FlexWrap | FlexWrap enumeration description |
| Enum | FocusPriority | Focus Priority |
| Enum | FoldStatus | Enumerates the fold status. |
| Enum | FontStyle | Text style |
| Enum | FontWeight | The font weight of the text |
| Enum | FormDimension | Defines the FormDimension enum. |
| Enum | FormRenderingMode | Defines the FormRenderingMode enum. |
| Enum | FormShape | Defines the FormShape enum. |
| Enum | FunctionKey | Function key for hot key. |
| Enum | GestureJudgeResult | Creating an Object |
| Enum | GestureMask | Creating an Object |
| Enum | GestureMode | Creating an Object |
| Enum | GesturePriority | Creating an Object |
| Enum | GestureRecognizerState | Creating an Object |
| Enum | GradientDirection | GradientDirection enumeration description |
| Enum | GridDirection | The enum of property layoutDirection |
| Enum | GridItemAlignment | Declare grid item alignment status |
| Enum | GridItemStyle | Defines the grid item style. |
| Enum | GridRowDirection | Defines the direction of grid-container component. |
| Enum | HeightBreakpoint | Type of window height breakpoint. |
| Enum | HitTestMode | Defines the hit test mode. |
| Enum | HorizontalAlign | HorizontalAlign enumeration description. |
| Enum | HoverEffect | HoverEffect enumeration description |
| Enum | HoverModeAreaType | Enumerates the type of area in hover mode. |
| Enum | IlluminatedType | Enum of Illuminated type |
| Enum | ImageAnalyzerType | Defines the image analyze type. |
| Enum | ImageContent | Specify image's content. |
| Enum | ImageFit | Image display mode. |
| Enum | ImageInterpolation |  |
| Enum | ImageRenderMode |  |
| Enum | ImageRepeat | ImageRepeat enumeration description |
| Enum | ImageRotateOrientation |  |
| Enum | ImageSize | ImageSize enumeration description |
| Enum | ImageSpanAlignment | The alignment of ImageSpan |
| Enum | ImmersiveMode | Define the immersive mode of all kind of dialog |
| Enum | IndexerAlign | indexer align property. |
| Enum | InputType | Declare the type of input box |
| Enum | InteractionHand | Function Called by Touch or Gesture. |
| Enum | ItemAlign | ItemAlign enumeration description |
| Enum | ItemState | ItemState |
| Enum | KeyProcessingMode | Key processing mode. Determines the priority of key event processing when compon |
| Enum | KeySource | Type of the input device that triggers the current key. |
| Enum | KeyType | Type of a key. |
| Enum | KeyboardAppearance | Defines keyboard appearance. |
| Enum | LaunchMode | Defines the mode of stack operation. |
| Enum | LayoutDirection | Defines the LayoutDirection of device. |
| Enum | LayoutMode | Enum for the layout mode of the content in the tab bar. |
| Enum | LayoutSafeAreaEdge | Enumerates the safe area edges can be ignored. |
| Enum | LayoutSafeAreaType | Enumerates the safe area types can be ignored. |
| Enum | LayoutStyle | Declare the layout style of the tab bar items. |
| Enum | LengthMetricsUnit | Enumerates the length metrics unit. |
| Enum | LengthUnit | Defines the Length Unit. |
| Enum | LevelMode | Define the display mode of all kind of dialog |
| Enum | LineBreakStrategy | Enum of line break strategy |
| Enum | LineCapStyle | LineCapStyle enumeration description |
| Enum | LineJoinStyle | Line Join Style |
| Enum | ListItemAlign | Declare list item alignment status |
| Enum | ListItemGroupArea | Declare list item group area |
| Enum | ListItemGroupStyle | Defines the list item group style. |
| Enum | ListItemStyle | Defines the list item style. |
| Enum | LoadingProgressStyle | Load style of progress bar. |
| Enum | LocalizedBarrierDirection | Specifies the localized direction value of Barrier. |
| Enum | LocationButtonOnClickResult | Enumerates the click event results of the location button. |
| Enum | LocationDescription | Enumerates the text that can be displayed on the location button. |
| Enum | LocationIconStyle | Enumerates the icon styles. |
| Enum | MarqueeDynamicSyncSceneType | Enum of scene type for Marquee |
| Enum | MarqueeUpdateStrategy | Marquee scrolling strategy after text update |
| Enum | MenuAlignType | The type of alignment between select and menu. |
| Enum | MenuPolicy | Define the menu pop-up policy |
| Enum | MenuPreviewMode | Defines the menu preview mode. |
| Enum | MenuType | Defines menu type. |
| Enum | ModalTransition | Defines modal transition type. |
| Enum | ModelType | The enum of model type |
| Enum | ModifierKey | Modifier key for hot key. |
| Enum | MouseAction | Function Called by Mouse |
| Enum | MouseButton | Function Called by Mouse |
| Enum | NavBarPosition | Navigation bar position |
| Enum | NavDestinationMode | NavDestination mode. |
| Enum | NavRouteMode | Define the route mode. |
| Enum | NavigationMode | Navigation mode |
| Enum | NavigationOperation | Defines the operation of current navigation transition. |
| Enum | NavigationSystemTransitionType | Types of system Transition. |
| Enum | NavigationTitleMode | Navigation title mode. |
| Enum | NavigationType | Route jump. |
| Enum | NestedScrollMode | Nested scroll nested mode |
| Enum | NodeRenderType | Render type of the node using for indicating that if the node will be shown on t |
| Enum | ObscuredReasons | ObscuredReasons. |
| Enum | OptionWidthMode | Decide whether the width of select menu fit the trigger or content |
| Enum | OutlineStyle | Outline Style |
| Enum | PageFlipMode | Page flip mode of Swiper and Tabs on mouse wheel event. |
| Enum | PanDirection | Creating an Object |
| Enum | PanelHeight | Enum for custom content display area. |
| Enum | PanelMode | Sets the initial state of the slidable panel. |
| Enum | PanelType | Sets the type of sliding panel. |
| Enum | ParticleEmitterShape | Enumerates the emitter shapes of a particle. |
| Enum | ParticleType | Enumerates the particle types. |
| Enum | ParticleUpdater | Enumerates the updater types of a particle. |
| Enum | PasteButtonOnClickResult | Enumerates the click event results of the paste button. |
| Enum | PasteDescription | Enumerates the text that can be displayed on the paste button. |
| Enum | PasteIconStyle | Enumerates the icon styles. |
| Enum | PatternLockChallengeResult | The challenge result based on input pattern for control pattern lock component. |
| Enum | PixelRoundCalcPolicy | Pixel Round Direction |
| Enum | Placement | Placement enumeration description |
| Enum | PlayMode | Play Mode |
| Enum | PlaybackSpeed | playback speed. |
| Enum | PreDragStatus | Defines the drag status before drag action. |
| Enum | ProgressStatus | Current status of progress bar. |
| Enum | ProgressStyle | Type of progress bar |
| Enum | ProgressType | Type of progress bar |
| Enum | RadioIndicatorType | Defines the IndicatorType of Radio component |
| Enum | RefreshStatus | The refresh status of the drop-down refresh. |
| Enum | RelateType | RelateType enumeration description |
| Enum | RenderFit | Enum of RenderFit |
| Enum | RepeatMode | Defines the Border Image Repeat Mode. |
| Enum | ResponseType | ResponseType for contextMenu |
| Enum | RichEditorDeleteDirection | Defines delete text direction. |
| Enum | RichEditorResponseType | ResponseType for contextMenu |
| Enum | RichEditorSpanType | Defines span type. |
| Enum | RouteType | Declare the jump method. |
| Enum | SafeAreaEdge | Enumerates the safe area edges. |
| Enum | SafeAreaType | Enumerates the safe area types. |
| Enum | SaveButtonOnClickResult | Enumerates the click event results of the save button. |
| Enum | SaveDescription | Enumerates the text that can be displayed on the save button. |
| Enum | SaveIconStyle | Enumerates the icon styles. |
| Enum | ScrollAlign | ScrollAlign. |
| Enum | ScrollBarDirection | Content scroll direction. |
| Enum | ScrollDirection | Content scroll direction. |
| Enum | ScrollSizeMode | Define the scroll size mode of the sheet. |
| Enum | ScrollSnapAlign | Declare limited position when scroll end. |
| Enum | ScrollSource | The possible source of scroll event |
| Enum | ScrollState | Declare scroll status |
| Enum | SearchType | Declare the type of search input box |
| Enum | SecurityComponentLayoutDirection | Enumerates the layout direction of the icon and text. |
| Enum | SeekMode | Seek mode. |
| Enum | SelectStatus | CheckboxGroup SelectStatus |
| Enum | SelectedMode | Enum for the mode of the tab bar when selected. |
| Enum | ShadowStyle | enum Shadow style |
| Enum | ShadowType | Define the type of shadow |
| Enum | SharedTransitionEffectType | SharedTransitionEffectType enumeration description |
| Enum | SheetKeyboardAvoidMode | Define the mode of sheet how to avoid keyboard. |
| Enum | SheetMode | Define the display mode of the sheet. |
| Enum | SheetSize | Defines sheet size type. |
| Enum | SheetType | Defines the sheet type. |
| Enum | SideBarContainerType | Sets the sidebar style of showing |
| Enum | SideBarPosition | Sets the sidebar position of showing |
| Enum | SizeType | Defines the size type. |
| Enum | SlideEffect | Declare the sliding effect of transition. |
| Enum | SliderBlockType | Declare SliderBlockType |
| Enum | SliderChangeMode | Declare SliderChangeMode |
| Enum | SliderInteraction | Declare SliderInteraction |
| Enum | SliderStyle | Declare sliderstyle |
| Enum | SourceTool | Defines the event tool type. |
| Enum | SourceType | Defines the event source type. |
| Enum | Sticky | Declare item ceiling attribute. |
| Enum | StickyStyle | Declare item group sticky style. |
| Enum | StyledStringKey | the attribute type of the StyledString |
| Enum | SubMenuExpandingMode | Declare SubMenuExpandingMode |
| Enum | SwipeActionState | Declare enum SwipeActionState. |
| Enum | SwipeDirection | Creating an Object |
| Enum | SwipeEdgeEffect | Sliding effect |
| Enum | SwiperAnimationMode | Declare the animation mode of SwiperController's changeIndex method. |
| Enum | SwiperDisplayMode | Declare the size of the swiper on the spindle. |
| Enum | SwiperDynamicSyncSceneType | Enum of SwiperDynamicSyncSceneType |
| Enum | SwiperNestedScrollMode | Swiper nested scroll nested mode |
| Enum | SymbolEffectStrategy | The symbol effect strategy. |
| Enum | SymbolRenderingStrategy | The symbol rendering strategy. |
| Enum | TextAlign | Alignment of text. |
| Enum | TextAreaType | Declare the type of input box |
| Enum | TextCase | Letter type in text |
| Enum | TextContentStyle | Text content style. |
| Enum | TextDataDetectorType | Defines the text data detector type. |
| Enum | TextDecorationStyle | Type of text decoration line style. |
| Enum | TextDecorationType | Type of text modifier. |
| Enum | TextDeleteDirection | Defines delete text direction. |
| Enum | TextHeightAdaptivePolicy | Enum of text height adaptation |
| Enum | TextInputStyle | Text input style. |
| Enum | TextOverflow | Declare how text overflows. |
| Enum | TextResponseType | ResponseType for contextMenu |
| Enum | TextSelectableMode | Type of text selectable. |
| Enum | TextSpanType | Defines span type. |
| Enum | ThemeColorMode | enum color mode |
| Enum | TimePickerFormat | Type of the TimePicker that need to be displayed. |
| Enum | TitleHeight | Title height. |
| Enum | ToggleType | Declare the type of status button |
| Enum | ToolbarItemStatus | Defines the status of toolbar item and it is used in the ToolbarItem interface. |
| Enum | TouchTestStrategy | Defines the touch test strategy object. |
| Enum | TouchType | Function Called by Touch |
| Enum | TransitionEdge | Defines the Edge object. |
| Enum | TransitionHierarchyStrategy | Source and target are two matched elements during the geometry transition. The a |
| Enum | TransitionType | TransitionType enumeration description. |
| Enum | VerticalAlign | VerticalAlign enumeration description |
| Enum | Visibility | Controls the display or hide of the current component |
| Enum | WaterFlowLayoutMode | Declare layout modes of WaterFlow. |
| Enum | Week | Set Weekend |
| Enum | WidthBreakpoint | Type of window width breakpoint. |
| Enum | WordBreak | Enum of word break |
| Enum | XComponentType | The type of XComponent |
| Interface | ASTCResource | Defines the resource which can use ASTC. |
| Interface | AbilityComponentInterface | Provide an interface for the ability component. |
| Interface | AbstractProperty | AbstractProperty can be understood as a handler or an alias to a property inside |
| Interface | AccessibilityHoverEvent | The accessibility hover action triggers this method invocation. |
| Interface | AccessibilityOptions | Defines the struct of AccessibilityOptions. |
| Interface | AlertDialogButtonOptions | Base button param used for AlertDialogParamWithOptions. |
| Interface | AlertDialogParam | Base param used for AlertDialog.show method. |
| Interface | AlertDialogParamWithButtons | Defines the dialog param with buttons. |
| Interface | AlertDialogParamWithConfirm | Defines the AlertDialog with confirm button. |
| Interface | AlertDialogParamWithOptions | Defines the dialog param with options. |
| Interface | AlignRuleOption | Defines the align rule options of relative container. |
| Interface | AlphabetIndexerInterface | Alphabet index bar. |
| Interface | AnimatableArithmetic | Define AnimatableArithmetic interface |
| Interface | AnimateOptions | AnimateOptions |
| Interface | AnimateParam | Defines the animate function params. |
| Interface | AnimateStyle | AnimateStyle |
| Interface | AnimationElement | animation element |
| Interface | AnimationOptions | Animation control options |
| Interface | AnimationResult | AnimationResult |
| Interface | AnimatorInterface | Defines Animator. |
| Interface | Application | Application |
| Interface | Area | Defines the area property. |
| Interface | ArrowStyle | Arrow object. |
| Interface | AttributeModifier | Defines the attribute modifier. |
| Interface | BackgroundBlurStyleOptions | Defines the options of backgroundBlurStyle |
| Interface | BackgroundBrightnessOptions | Define BackgroundBrightness Options. |
| Interface | BackgroundEffectOptions | Defines the options of BackgroundEffect |
| Interface | BadgeInterface | Defines Badge Component. |
| Interface | BadgeParam | Defines the base param of badge. |
| Interface | BadgeParamWithNumber | Defines the badge param with count and maxCount. |
| Interface | BadgeParamWithString | Defines the badge param with string value. |
| Interface | BadgeStyle | BadgeStyle object |
| Interface | BarGridColumnOptions | Provides an interface for the grid column options of an tab bar including sm, md |
| Interface | BarrierStyle | Specifies the BarrierStyle of relative container |
| Interface | BaseEvent | Defines the base event. |
| Interface | BaseGestureEvent | Defines the gesture base event. |
| Interface | BaseHandlerOptions | Defines the BaseHandlerOptions options. |
| Interface | Bias | Defines the Bias. |
| Interface | BindOptions | Overlay module options |
| Interface | BlankInterface | Create Blank. |
| Interface | BlurOptions | Defines the options of blur |
| Interface | BlurStyleOptions | Defines the options of blurStyle |
| Interface | BoardStyle | Provide an interface for the style of an indicator including border radius |
| Interface | BorderImageOption | Border image option |
| Interface | BorderOptions | Defines the options of border. |
| Interface | BreakPoints | Defines the breakpoints of grid-row component. |
| Interface | BuildOptions | BuildOptions info. |
| Interface | ButtonConfiguration | ButtonConfiguration used by button content modifier. |
| Interface | ButtonElement | The <button> component includes capsule, circle, text, arc, and download buttons |
| Interface | ButtonInterface | Defines the Button Component. |
| Interface | ButtonOptions | Defines the button options. |
| Interface | ButtonStyle | Sets the control button style |
| Interface | CalendarDay | Provides a monthly view component to display information such as date, shift bre |
| Interface | CalendarDialogOptions | Defines the DatePickerDialogOptions for Calendar Picker Dialog. |
| Interface | CalendarInterface | Calendar Interface |
| Interface | CalendarOptions | Defines the options of CalendarPicker. |
| Interface | CalendarPickerInterface | Defines the CalendarPicker Component. |
| Interface | CalendarRequestedData | Defines the struct of CalendarRequestedData. |
| Interface | CalendarSelectedDate | Defines the struct of CalendarSelectedDate. |
| Interface | CallAbilityParam |  |
| Interface | Callback | Defines the window callback. |
| Interface | CameraElement | The <camera> component provides preview and photographing functions. |
| Interface | CameraTakePhotoOptions | CameraTakePhotoOptions |
| Interface | CancelButtonOptions | Defines the CancelButton options |
| Interface | CancelButtonSymbolOptions | Defines the CancelButton symbol options |
| Interface | CanvasElement | <canvas> provides a rectangular canvas component for drawing graphics on the scr |
| Interface | CanvasGradient | You can create a gradient object on the canvas by calling CanvasRenderingContext |
| Interface | CanvasInterface | TextTimer component, which provides the text timer capability. |
| Interface | CanvasPattern | Describes an opaque object of a template, which is created using the createPatte |
| Interface | CanvasRenderingContext2D | CanvasRenderingContext2D allows you to draw rectangles, text, images, and other  |
| Interface | CapsuleStyleOptions | Defines the capsule style Options. |
| Interface | CaretOffset | CaretOffset info. |
| Interface | CaretStyle | Defines the cursor style |
| Interface | ChainAnimationOptions | Defines the chain animation options. |
| Interface | ChainWeightOptions | Defines the ChainWeightOptions interface. |
| Interface | ChartElement | The <chart> component displays line charts, gauge charts, and bar charts. |
| Interface | CheckBoxConfiguration | CheckBoxConfiguration used by content modifier. |
| Interface | CheckboxGroupInterface | Provides an interface for the CheckboxGroup component. |
| Interface | CheckboxGroupOptions | Defines the options of CheckboxGroup. |
| Interface | CheckboxGroupResult | Defines the options of CheckboxGroupResult. |
| Interface | CheckboxInterface | Provides an interface for the Checkbox component. |
| Interface | CheckboxOptions | Defines the options of Checkbox. |
| Interface | Circle | Defines the Circle. |
| Interface | CircleInterface | Defines circle component. |
| Interface | CircleOptions | Defines circle options for Circle component. |
| Interface | CircleStyleOptions | Defines the options of active circle style. |
| Interface | ClickEffect | Defines the click effect. |
| Interface | ClickEvent | The tap action triggers this method invocation. |
| Interface | CloseSwipeActionOptions | Defines the close swipe action options. |
| Interface | Colors | Defines the struct of Colors. |
| Interface | ColumnInterface | Defines the Column Component. |
| Interface | ColumnSplitDividerStyle | Provides an interface for the style of a divider including start margin and end  |
| Interface | ColumnSplitInterface | Defines the ColumnSplit component. |
| Interface | CommandPath | Defines the CommandPath. |
| Interface | CommonConfiguration | Defines the common configuration. |
| Interface | CommonInterface | CommonInterface for ide. |
| Interface | CommonProgressStyleOptions | Progress common style options. |
| Interface | Component3DInterface | Defines Component3D. |
| Interface | ComponentOptions | Defines the options of Component ClassDecorator. |
| Interface | ComputedBarAttribute | The attribute of scrollbar to compute scrollbar position and height. |
| Interface | Configuration | Defines the data type of the interface restriction. |
| Interface | ConstraintSizeOptions | Defines the constrain size options. |
| Interface | ContainerSpanInterface | Span container interface. |
| Interface | ContentCoverOptions | Component content cover options |
| Interface | ContentModifier | Defines the content modifier. |
| Interface | ContentSlotInterface | Placeholder component for NodeContent and ComponentContent |
| Interface | ContextAttrOptions | ContextAttrOptions |
| Interface | ContextMenuAnimationOptions | Defines the ContextMenu's preview animator options. |
| Interface | ContextMenuOptions | Defines the context menu options. |
| Interface | CopyEvent | the callback of copy event. |
| Interface | Corners | Defines the Corner property. |
| Interface | CounterInterface | Counter component, which provides corresponding increment or decrement counting  |
| Interface | CrossLanguageOptions | Defines the cross-language options. |
| Interface | CurrentDayStyle | CurrentDayStyle object. |
| Interface | CurrentOffsetResultValue | CurrentOffsetResultValue |
| Interface | CustomDialogControllerOptions | Defines the options of CustomDialogController. |
| Interface | CustomPopupOptions | Defines the custom popup options. |
| Interface | CustomSpanDrawInfo | Defines the CustomSpanDrawInfo interface. |
| Interface | CustomSpanMeasureInfo | Defines the CustomSpanMeasureInfo interface. |
| Interface | CustomSpanMetrics | Defines the CustomSpanMetrics interface. |
| Interface | CustomTheme | Defines the struct of CustomTheme. |
| Interface | CutEvent | the callback of cut event. |
| Interface | DataAddOperation | Defines add operation. |
| Interface | DataChangeListener | Data Change Listener. |
| Interface | DataChangeOperation | Defines change operation. |
| Interface | DataDeleteOperation | Defines delete operation. |
| Interface | DataExchangeOperation | Defines exchange operation. |
| Interface | DataMoveOperation | Defines move&exchange operation. |
| Interface | DataPanelConfiguration | DataPanelConfiguration used by dataPanel content modifier |
| Interface | DataPanelInterface | Defines the DataPanel component. |
| Interface | DataPanelOptions | Defines the options of DataPanel. |
| Interface | DataPanelShadowOptions | Defines the options of Shadow. |
| Interface | DataReloadOperation | Defines reload operation. |
| Interface | DatePickerDialogOptions | Defines the DatePickerDialogOptions for Data Picker Dialog. |
| Interface | DatePickerInterface | Defines the DatePicker Component. |
| Interface | DatePickerOptions | Defines the options of DatePicker. |
| Interface | DatePickerResult | Defines the struct of DatePickerResult. |
| Interface | DecorationStyleInterface | DecorationStyleInterface |
| Interface | DecorationStyleResult | Defines the font decoration result. |
| Interface | DeleteValue | Provides an interface for deleting value from text. |
| Interface | DialogElement | The <dialog> component is a custom pop-up container. |
| Interface | DirectionalEdgesT | Defines the DirectionalEdgesT interface. |
| Interface | DismissContentCoverAction | Component content cover dismiss |
| Interface | DismissDialogAction | Component dialog dismiss action. |
| Interface | DismissPopupAction | Component popup dismiss |
| Interface | DismissSheetAction | Component sheet dismiss |
| Interface | DisturbanceFieldOptions | Defines particle disturbance Field params. |
| Interface | DivElement | The <div> component provides a div container. |
| Interface | DividerInterface | Provides a divider component to separate different content blocks/content elemen |
| Interface | DividerOptions | Defines the struct of DividerOptions. |
| Interface | DividerStyle | Provides an interface for the style of an divider including stroke width, color, |
| Interface | DividerStyleOptions | Defines the struct of DividerStyleOptions. |
| Interface | DragEvent | DragEvent object description |
| Interface | DragInteractionOptions | Defines the drag options. |
| Interface | DragItemInfo | DragItemInfo object description |
| Interface | DragPreviewOptions | Defines the preview options. |
| Interface | DropOptions | Defines the options for the drop handling. |
| Interface | EclipseStyleOptions | Defines the Eclipse style Options. |
| Interface | EdgeEffectOptions | Define EdgeEffect Options. |
| Interface | Edges | Defines the Edge property. |
| Interface | EditMenuOptions | EditMenuOptions |
| Interface | EditableTextChangeValue | Define the editableText Component changed value. |
| Interface | EffectComponentInterface | Provides an Effect Component, which is invisible, but setting properties on this |
| Interface | Element | Element |
| Interface | ElementReferences | Element References |
| Interface | EllipseInterface | Ellipse drawing. |
| Interface | EmbeddedComponentInterface | Provide an interface for the EmbeddedComponent, which is used <br/>to render UI  |
| Interface | EmitterOptions | Defines the emitter Options. |
| Interface | EmitterProperty | Defines the emitter property. |
| Interface | EntryOptions | Defines the options of Entry ClassDecorator. |
| Interface | EnvPropsOptions | EnvProps object |
| Interface | EventTarget | Defines the event target. |
| Interface | ExchangeIndex | Defines position of exchange data. |
| Interface | ExchangeKey | Defines new key of exchange data. |
| Interface | ExpectedFrameRateRange | Interface for ExpectedFrameRateRange. |
| Interface | FadingEdgeOptions | Defines the fadingEdge options. |
| Interface | FingerInfo | Type of the finger information. |
| Interface | FinishWithResultParams |  |
| Interface | FlexInterface | Provides a monthly view component to display information such as date, shift bre |
| Interface | FlexOptions | Defines the options of Flex. |
| Interface | FlexSpaceOptions | The space to be inserted, either horizontally or vertically, between two adjacen |
| Interface | FlowItemInterface | Mesh container for static fixed-size layout scenarios. |
| Interface | FocusAxisEvent | Focus axis event object description. |
| Interface | FocusBoxStyle | Focus box style. |
| Interface | FocusParamObj | Defines the focus param. |
| Interface | FolderStackInterface | Provides ports for stacking containers. |
| Interface | Font | Defines the font used for text. |
| Interface | FontSettingOptions | Defines the options of font. |
| Interface | ForEachInterface | looping function. |
| Interface | ForegroundBlurStyleOptions | Defines the options of ForegroundBlurStyle |
| Interface | ForegroundEffectOptions | Defines the options of ForegroundEffect |
| Interface | FormCallbackInfo | Defines the FormCallbackInfo. |
| Interface | FormComponentInterface | Defines the FormComponent. |
| Interface | FormInfo | Defines the FormInfo. |
| Interface | FormLinkInterface | Defines the FormLink interface. |
| Interface | FormLinkOptions | Defines the FormLink options. |
| Interface | Frame | Frame info, include the position info and size info. |
| Interface | GaugeConfiguration | GaugeConfiguration used by content modifier |
| Interface | GaugeIndicatorOptions | Defines the options of gauge indicator. |
| Interface | GaugeInterface | Defines the Gauge component. |
| Interface | GaugeShadowOptions | Defines the options of gauge track shadow. |
| Interface | GeometryInfo | Sub component layout info. |
| Interface | GeometryTransitionOptions | Defines the options of geometry transition. |
| Interface | GestureEvent | Defines event info for gesture. |
| Interface | GestureGroupGestureHandlerOptions | Defines the GestureGroupGestureHandler options. |
| Interface | GestureGroupInterface | Defines the GestureGroup interface. |
| Interface | GestureInfo | The description of gesture information. |
| Interface | GestureInterface | Defines Gesture interface. |
| Interface | GestureModifier | Defines the gesture modifier. |
| Interface | GestureStyleInterface | Defines the Gesture Events. |
| Interface | GridColColumnOption | Defines the option in number unit of grid-container child component. |
| Interface | GridColInterface | Defines the the new version of grid-container child component. |
| Interface | GridColOptions | Defines the options of grid-container child component. |
| Interface | GridContainerInterface | Defines the GridContainer component. |
| Interface | GridContainerOptions | Defines the options of GridContainer. |
| Interface | GridInterface | Defines the grid interface. |
| Interface | GridItemInterface | Mesh container for static fixed-size layout scenarios. |
| Interface | GridItemOptions | Defines the grid item options. |
| Interface | GridLayoutOptions | The options to help grid layout |
| Interface | GridRowColumnOption | Defines the option in number unit of grid-container component. |
| Interface | GridRowInterface | Defines the the new version of grid-container component. |
| Interface | GridRowOptions | Defines the options of grid-row component. |
| Interface | GridRowSizeOption | Defines the option in length unit of grid-row component. |
| Interface | GuideLinePosition | Specifies the position of guideLine |
| Interface | GuideLineStyle | Specifies the GuideLineStyle of relative container |
| Interface | GutterOption | Defines the gutter of grid-row component. |
| Interface | HistoricalPoint | TouchObject getHistoricalPoints Function Parameters |
| Interface | HoverEvent | The hover action triggers this method invocation. |
| Interface | HoverEventParam | Defines the Embed Data info. |
| Interface | HyperlinkInterface | Defines the hyperlink interface. |
| Interface | ICurve | Interface for curve object. |
| Interface | IDataSource | Developers need to implement this interface to provide data to LazyForEach compo |
| Interface | IDataSourcePrefetching | Implement this interface to provide data prefetching for the LazyForEach compone |
| Interface | IMonitor | Define IMonitor interface |
| Interface | IMonitorValue | Define IMonitorValue interface |
| Interface | IPrefetcher | Implement this interface to provide prefetcher logic. |
| Interface | IPropertySubscriber | Provides an interface for attribute subscribers. |
| Interface | ISinglePropertyChangeSubscriber | Defines the subscriber. |
| Interface | IconOptions | Defines the icon options |
| Interface | ImageAIOptions | Image ai options. |
| Interface | ImageAnalyzerConfig | Image analyzer config. |
| Interface | ImageAnimatorElement | Image animator element |
| Interface | ImageAnimatorInterface | Defines the ImageAnimator Interface. |
| Interface | ImageAttachmentInterface | Defines the ImageAttachmentInterface. |
| Interface | ImageAttachmentLayoutStyle | Defines the  ImageAttachment Layout Style. |
| Interface | ImageError |  |
| Interface | ImageFrameInfo | Defines the ImageFrameInfo Interface. |
| Interface | ImageInterface |  |
| Interface | ImageLoadResult | The information about the successfully loaded image. |
| Interface | ImageParticleParameters | Defines the parameters for an image-like particle. |
| Interface | ImageSpanInterface | Provide image decoration in the text component. |
| Interface | IndicatorComponentInterface | Provides an interface for indicator. |
| Interface | IndicatorStyle | Provide an interface for the style of an indicator including color, height, widt |
| Interface | InputCounterOptions | Define the ratio of characters entered by the the percentage of InputCounterOpti |
| Interface | InputElement | The <input> component provides an interactive interface to receive user input, w |
| Interface | InsertValue | Defines the inserted text value info. |
| Interface | InvertOptions | Define the options of invert |
| Interface | IsolatedOptions | This interface is used to set the options for IsolatedComponentAttribute during  |
| Interface | ItemDragInfo | ItemDragInfo object description |
| Interface | KeyEvent | KeyEvent object description: |
| Interface | KeyboardOptions | Defines the custom keyboard options of RichEditor. |
| Interface | KeyframeAnimateParam | Defines the overall animation parameters of the keyframe animation. |
| Interface | KeyframeState | Defines a keyframe state. |
| Interface | LabelStyle | LabelStyle object. |
| Interface | LayoutBorderInfo | Sub component border info. |
| Interface | LayoutChild | Sub component info passed from framework when layout and measure happens. |
| Interface | LayoutConstraint | Layout constraint, include the max size, the min size and the reference size for |
| Interface | LayoutInfo | Sub component layout info. |
| Interface | LayoutManager | Define the LayoutManager for querying layout information. |
| Interface | Layoutable | Sub component info passed from framework when layout happens. |
| Interface | LazyForEachInterface | Lazy loading. |
| Interface | LeadingMarginPlaceholder | Defines the leading margin placeholder of a paragraph. |
| Interface | LightSource | LightSource info |
| Interface | LineInterface | Line drawing component. |
| Interface | LinearGradient | Linear Gradient Interface |
| Interface | LinearGradientBlurOptions | Linear Gradient Blur Interface |
| Interface | LinearStyleOptions | Defines the linear style Options. |
| Interface | ListElement | List element |
| Interface | ListInterface | The list interface is extended. |
| Interface | ListItemGroupInterface | Defines the ListItemGroup component |
| Interface | ListItemGroupOptions | Defines the list item group options. |
| Interface | ListItemInterface | Values in the list |
| Interface | ListItemOptions | Defines the list item options. |
| Interface | ListScrollToOptions | List scroll to options |
| Interface | LoadingProgressConfiguration | LoadingProgressConfiguration used by LoadingProgress contentModifier |
| Interface | LoadingProgressInterface | Provides an interface for extending the loading progress. |
| Interface | LocalizedAlignRuleOptions | Defines the Localized align rule options of relative container. |
| Interface | LocalizedBarrierStyle | Specifies the Localized BarrierStyle of relative container |
| Interface | LocalizedBorderRadiuses | Defines the localized border radius property. |
| Interface | LocalizedEdgeColors | Defines the localized border color property. |
| Interface | LocalizedEdgeWidths | Defines the localized border width property. |
| Interface | LocalizedEdges | Defines the LocalizedEdges. |
| Interface | LocalizedHorizontalAlignParam | Defines the localized horizontal align param of relative container. |
| Interface | LocalizedPadding | Defines the localized padding property. |
| Interface | LocalizedPosition | Defines the LocalizedPosition. |
| Interface | LocalizedVerticalAlignParam | Defines the localized vertical align param of relative container. |
| Interface | LocationButtonInterface | Defines the interface for setting a location button. |
| Interface | LocationButtonOptions | Declares the interface for setting the location button options. |
| Interface | LongPressGestureEvent | Defines event info for long press gesture. |
| Interface | LongPressGestureHandlerOptions | Defines the LongPressGestureHandler options. |
| Interface | LongPressGestureInterface | Defines LongPressGesture interface extends GestureInterface<LongPressGestureInte |
| Interface | LunarSwitchStyle | Provide an interface for the lunar switch style of DatePickerDialog |
| Interface | MarkStyle | Define the style of checkbox mark. |
| Interface | MarqueeElement | The <marquee> component inserts scrolling text, which is displayed in a single l |
| Interface | MarqueeInterface | Provides the interface for the marquee attributes. |
| Interface | Measurable | Sub component info passed from framework when measure happens. |
| Interface | MeasureResult | Sub component MeasureResult info. |
| Interface | MediaCachedImageInterface |  |
| Interface | MenuElement | The <menu> component provides menus as temporary pop-up windows to display opera |
| Interface | MenuInterface | Defines the Menu Component. |
| Interface | MenuItemConfiguration | MenuItemConfiguration used by menu item content modifier. |
| Interface | MenuItemGroupInterface | Defines the MenuItemGroup Component. |
| Interface | MenuItemGroupOptions | Defines the option of MenuItemGroup. |
| Interface | MenuItemInterface | Defines the MenuItem Component. |
| Interface | MenuItemOptions | Defines the option of MenuItem. |
| Interface | MenuOptions | Defines the menu options. |
| Interface | MonthData | Date object. |
| Interface | MotionBlurAnchor | Define motion blur anchor coordinates. |
| Interface | MotionBlurOptions | Define motion blur options. |
| Interface | MotionPathOptions | Defines the motion path options. |
| Interface | MouseEvent | The mouse click action triggers this method invocation. |
| Interface | MoveIndex | Defines position of moved data. |
| Interface | MultiShadowOptions | Defines the options of Shadow. |
| Interface | NavContentInfo | Navigation content info. |
| Interface | NavDestinationCommonTitle | Defines the navigation destination common title. |
| Interface | NavDestinationContext | Indicates the context of NavDestination. |
| Interface | NavDestinationCustomTitle | Defines the navigation destination custom title. |
| Interface | NavDestinationInterface | The construct function of NavDestination. |
| Interface | NavDestinationTransition | NavDestination animation protocol. |
| Interface | NavRouterInterface | The construct function of NavRouter. |
| Interface | NavigationAnimatedTransition | Navigation transition animation protocol. |
| Interface | NavigationCommonTitle | Defines the navigation common title. |
| Interface | NavigationCustomTitle | Defines the navigation custom title. |
| Interface | NavigationInterception | Provide navigation transition interception |
| Interface | NavigationInterface | Provide navigator view interface |
| Interface | NavigationMenuItem | Navigation menu item, include menu icon and menu info |
| Interface | NavigationOptions | Indicates the options of stack operation. |
| Interface | NavigationTitleOptions | Indicates the options of Navigation's Titlebar. |
| Interface | NavigationToolbarOptions | Indicates the options of Navigation's Toolbar. |
| Interface | NavigationTransitionProxy | Navigation transition proxy. |
| Interface | NavigatorInterface | Create route |
| Interface | NestedScrollInfo | Indicates the nested scrollable container components. |
| Interface | NestedScrollOptions | Define nested scroll options |
| Interface | NodeContainerInterface | Defines the Interface of NodeContainer. To display the node build by an associat |
| Interface | NonCurrentDayStyle | Non current day style. |
| Interface | OffscreenCanvasRenderingContext2D | Provides a 2D rendering context for the drawing surface of the < Canvas > elemen |
| Interface | OffsetOptions | OffsetOptions info. |
| Interface | OffsetResult | OffsetResult info. |
| Interface | Options | Options type |
| Interface | OutlineOptions | Defines the options of border. |
| Interface | OverlayManagerOptions | the property of OverlayManager. |
| Interface | OverlayOffset | Defines the OverlayOffset. |
| Interface | OverlayOptions | Defines the OverlayOptions interface. |
| Interface | PageInfo | Defines the PageInfo type. The value of routerPageInfo indicates the information |
| Interface | PageTransitionEnterInterface | Provides an interface to set transition style when a page enters. |
| Interface | PageTransitionExitInterface | Provide an interface to set transition style when a page exits. |
| Interface | PageTransitionOptions | Defines pageTransition constructor parameters. |
| Interface | PanGestureEvent | Defines event info for pan gesture. |
| Interface | PanGestureHandlerOptions | Defines the PanGestureHandler options. |
| Interface | PanGestureInterface | Defines PanGesture interface extends GestureInterface<PanGestureInterface>. |
| Interface | PanelInterface | Provides a sliding panel interface. |
| Interface | ParagraphStyleInterface | ParagraphStyleInterface |
| Interface | ParticleColorPropertyOptions | Defines the particle color property updater configs which can support generics. |
| Interface | ParticleColorPropertyUpdaterConfigs | Defines the particle color property updater configs. |
| Interface | ParticleConfigs | Defines the particle configs. |
| Interface | ParticleInterface | Defines the particle Interface. |
| Interface | ParticleOptions | Defines the ParticleOptions Interface. |
| Interface | ParticlePropertyAnimation | Defines the particle property lifecycle. |
| Interface | ParticlePropertyOptions | Defines the particle property Options. |
| Interface | ParticlePropertyUpdaterConfigs | Defines the particle property updater configs. |
| Interface | PasswordIcon | PasswordIcon object. |
| Interface | PasteButtonInterface | Defines the interface for setting a paste button. |
| Interface | PasteButtonOptions | Declares the interface for setting the paste button options. |
| Interface | PasteEvent | Defines the paste event. |
| Interface | Path2D | Path2D |
| Interface | PathInterface | Provides the path drawing interface. |
| Interface | PathShapeOptions | Interface for PathShape constructor parameters. |
| Interface | PatternLockInterface | Provides an interface for generating PatternLock. |
| Interface | PersistPropsOptions | PersistProps object |
| Interface | PickerDialogButtonStyle | Provide an interface for the button style of picker |
| Interface | PickerElement | The <picker> component supports common, date, time, and multi-column text select |
| Interface | PickerTextStyle | Provide an interface for the text style of picker |
| Interface | PinchGestureEvent | Defines event info for pinch gesture. |
| Interface | PinchGestureHandlerOptions | Defines the PinchGestureHandler options. |
| Interface | PinchGestureInterface | Defines PinchGesture interface extends GestureInterface<PinchGestureInterface>. |
| Interface | PixelMapMock | pixelmap object with release function. |
| Interface | PixelRoundPolicy | Defines the pixel round property. |
| Interface | PixelStretchEffectOptions | Set the edge blur effect distance of the corresponding defense line of the compo |
| Interface | PlaceholderStyle | Defines the placeholder style. |
| Interface | PluginComponentInterface | Provides plugin component. |
| Interface | PointLightStyle | PointLightStyle info |
| Interface | PointParticleParameters | Defines the parameters for a point-like particle. |
| Interface | PolygonInterface | Provides the polygon drawing interface. |
| Interface | PolylineInterface | Provides an interface for drawing polylines. |
| Interface | PopInfo | Indicates the information of the popped page. |
| Interface | PopupMessageOptions | Defines the options of popup message. |
| Interface | PopupOptions | Defines the popup options. |
| Interface | Position | Defines the position. |
| Interface | PositionWithAffinity | Position and affinity. |
| Interface | PreviewConfiguration | Defines the drag preview configuration. |
| Interface | PreviewParams | Define Preview property |
| Interface | PreviewText | The previewText. |
| Interface | ProgressConfiguration | ProgressConfiguration used by progress contentModifier |
| Interface | ProgressInterface | Provides the progress bar interface. |
| Interface | ProgressOptions | Defines the option of Progress. |
| Interface | ProgressStyleMap | Defines the map for progress type and style. |
| Interface | ProgressStyleOptions | Defines style options for progress component. |
| Interface | ProvideOptions | Defines the options of Provide PropertyDecorator. |
| Interface | QRCodeInterface | Provides an interface for generating QR codes. |
| Interface | RRect | Round rect. |
| Interface | RadioConfiguration | RadioConfiguration used by radio Configuration |
| Interface | RadioInterface | Provides an interface for creating a radio box. |
| Interface | RadioOptions | Input parameter for creating a radio box. |
| Interface | RadioStyle | Set radio Style. |
| Interface | RatingConfiguration | RatingConfiguration used by rating content modifier. |
| Interface | RatingInterface | Provides the interface for scoring bars. |
| Interface | RectInterface | Provides an interface for drawing rectangles. |
| Interface | RectObj | RectObj |
| Interface | RectResult | Rect info. |
| Interface | RectShapeOptions | Interface for RectShape constructor parameters. |
| Interface | Rectangle | Defines the data type of the interface restriction. |
| Interface | RefreshInterface | Provides a pull-down refresh interface. |
| Interface | RefreshOptions | Defines the options of refresh component. |
| Interface | RelativeContainerInterface | Provides ports for relative containers. |
| Interface | RemoteWindowInterface | Provides an interface for controlling the remote window. |
| Interface | RenderOptions | RenderOptions info. |
| Interface | RepeatItem | Construct a new type for each item. |
| Interface | RequestParams |  |
| Interface | ResizableOptions | Image resizable options |
| Interface | ResourceImageAttachmentOptions | Defines the ResourceImageAttachmentOptions. |
| Interface | Result |  |
| Interface | RichEditorBuilderSpanOptions | Defines the builder span options of RichEditor. |
| Interface | RichEditorChangeValue | Provides an interface for changes in the text. |
| Interface | RichEditorDeleteValue | Provides an interface for deleting value from text. |
| Interface | RichEditorGesture | Defines the richEditor Gestures. |
| Interface | RichEditorImageSpan | Defines the image span. |
| Interface | RichEditorImageSpanOptions | Defines the image span options of RichEditor. |
| Interface | RichEditorImageSpanResult | Defines the image span. |
| Interface | RichEditorImageSpanStyle | Defines the span image style. |
| Interface | RichEditorImageSpanStyleResult | Defines the span image style result. |
| Interface | RichEditorInsertValue | Defines the inserted text value info. |
| Interface | RichEditorInterface | Provides an interface for writing texts. |
| Interface | RichEditorLayoutStyle | Defines the richEditor Image Layout Style. |
| Interface | RichEditorOptions | Defines the options of RichEditor. |
| Interface | RichEditorParagraphResult | Defines the paragraph result. |
| Interface | RichEditorParagraphStyle | Defines the paragraph style. |
| Interface | RichEditorParagraphStyleOptions | Defines paragraph style option of RichEditor. |
| Interface | RichEditorRange | Defines range of RichEditor. |
| Interface | RichEditorSelection | Defines the text information for editing. |
| Interface | RichEditorSpanPosition | Defines the span position. |
| Interface | RichEditorSpanStyleOptions | Defines span style option of RichEditor. |
| Interface | RichEditorStyledStringOptions | Defines the options of RichEditor with StyledString. |
| Interface | RichEditorSymbolSpanOptions | Defines the symbol span options of RichEditor. |
| Interface | RichEditorSymbolSpanStyle | Defines the symbol span style. |
| Interface | RichEditorSymbolSpanStyleResult | Defines the symbol span style result. |
| Interface | RichEditorTextSpan | Defines the text span. |
| Interface | RichEditorTextSpanOptions | Defines the span options of RichEditor. |
| Interface | RichEditorTextSpanResult | Defines the text span result. |
| Interface | RichEditorTextStyle | Defines the span text style. |
| Interface | RichEditorTextStyleResult | Defines the text style result. |
| Interface | RichEditorUpdateImageSpanStyleOptions | Defines image span style option of RichEditor. |
| Interface | RichEditorUpdateSymbolSpanStyleOptions | Defines symbol span style option of RichEditor. |
| Interface | RichEditorUpdateTextSpanStyleOptions | Defines text span style option of RichEditor. |
| Interface | RichTextInterface | Provides an interface for RichText component. |
| Interface | RingStyleOptions | Defines the ring style Options. |
| Interface | RootSceneInterface | Defines the interface of RootScene. |
| Interface | RootSceneSession | Defines the session of RootScene. |
| Interface | RotateOptions | The param of rotate. |
| Interface | RotationGestureEvent | Defines event info for rotation gesture. |
| Interface | RotationGestureHandlerOptions | Defines the RotationGestureHandler options. |
| Interface | RotationGestureInterface | Defines RotationGesture interface extends GestureInterface<RotationGestureInterf |
| Interface | RoundRect | Defines the RoundRect. |
| Interface | RoundRectShapeOptions | Interface for RectShape constructor parameters with separate radius values. |
| Interface | RouteInfo | Indicates the information of the route page. |
| Interface | RouteMapConfig | Indicates configuration info of destination. |
| Interface | RowInterface | The components are laid out horizontally |
| Interface | RowSplitInterface | Provides interfaces for layout in the vertical direction. |
| Interface | SaveButtonInterface | Defines the interface for setting a save button. |
| Interface | SaveButtonOptions | Declares the interface for setting the save button options. |
| Interface | ScaleOptions | Defines the options of scale. |
| Interface | ScaleRingStyleOptions | Defines the ScaleRing style Options. |
| Interface | ScanEffectOptions | Defines the enable scan effect. |
| Interface | SceneOptions | Scene options used by 3D scene control |
| Interface | ScreenInterface | Defines the interface of Screen. |
| Interface | ScrollAnimationOptions | Provides custom animation parameters. |
| Interface | ScrollBarInterface | Provides interfaces for scroll bar. |
| Interface | ScrollBarOptions | Defines the options of ScrollBar. |
| Interface | ScrollEdgeOptions | Define scroll edge options |
| Interface | ScrollInterface | Provides interfaces for scrollable containers. |
| Interface | ScrollOffset | ScrollOffset |
| Interface | ScrollOptions | ScrollOptions |
| Interface | ScrollPageOptions | Define scroll page options |
| Interface | ScrollParam | ScrollParam |
| Interface | ScrollSnapOptions | Define scroll snap options |
| Interface | ScrollToIndexOptions | Define scrollToIndex options |
| Interface | ScrollableBarModeOptions | Provides an interface for the options for the scrollable bar mode including marg |
| Interface | SearchButtonOptions | Defines the SearchButton options |
| Interface | SearchInterface | The construct function of search |
| Interface | SelectInterface | Provides the select interface. |
| Interface | SelectOption | The declare of selectOption. |
| Interface | SelectionMenuOptions | Defines the selection menu options. |
| Interface | SelectionOptions | Defines the selection options. |
| Interface | SendMessageOptions |  |
| Interface | ShadowOptions | Define the options of shadow |
| Interface | ShapeInterface | Provides interfaces for drawing components. |
| Interface | ShapeSize | Interface for shape size properties. |
| Interface | SheetDismiss | Component sheet dismiss |
| Interface | SheetOptions | Component sheet options |
| Interface | SheetTitleOptions | Component sheet title options |
| Interface | SideBarContainerInterface | The construct function of sidebar |
| Interface | Size | Size info. |
| Interface | SizeOptions | Defines the size options. |
| Interface | SizeResult | Sub component SizeResult info. |
| Interface | SizeT | Defines the Size property. |
| Interface | SlideRange | Defines the valid slidable range. If and only if MIN <= from <= to <= MAX, slidi |
| Interface | SliderBlockStyle | Defines the style of slider block. |
| Interface | SliderConfiguration | SliderConfiguration used by slider content modifier |
| Interface | SliderInterface | Provides an interface for the slide bar component. |
| Interface | SliderOptions | Defines the options of Slider. |
| Interface | SpanInterface | Provide text decoration. |
| Interface | SpanStyle | SpanStyle |
| Interface | SpringBackAction | Defines sheet spring back action |
| Interface | StackInterface | Provides ports for stacking containers. |
| Interface | StateStyles | Component State Styles. |
| Interface | StepperInterface | Declare the stepper. |
| Interface | StepperItemInterface | Provides an interface for switching the stepperItem view on stepper container. |
| Interface | StyleOptions | StyleOptions |
| Interface | StyledStringChangeValue | Define the StyledString changed value. |
| Interface | StyledStringChangedListener | Define the StyledString changed listener. |
| Interface | StyledStringController | Define the StyledString controller. |
| Interface | SubmitEvent | Provides the method of keeping TextInput editable state when submitted. |
| Interface | SubscribeAbilityEventParam |  |
| Interface | SubscribeMessageOptions |  |
| Interface | SubscribeMessageResponse |  |
| Interface | SurfaceRect | Surface Rectangle information. |
| Interface | SurfaceRotationOptions | Surface rotation options. |
| Interface | SwipeActionItem | Defines the swipe action item for SwipeActionOptions. |
| Interface | SwipeActionOptions | Defines the SwipeActionOption of swipeAction attribute method. |
| Interface | SwipeGestureEvent | Defines event info for swipe gesture. |
| Interface | SwipeGestureHandlerOptions | Defines the SwipeGestureHandler options. |
| Interface | SwipeGestureInterface | Defines SwipeGesture interface extends GestureInterface<SwipeGestureInterface>. |
| Interface | SwiperAnimationEvent | Provides an interface for swiper animation. |
| Interface | SwiperContentAnimatedTransition | Defines the swiper content animated transition options. |
| Interface | SwiperContentTransitionProxy | The proxy of SwiperContentAnimatedTransition. |
| Interface | SwiperContentWillScrollResult | The result of swiper ContentWillScrollCallback. |
| Interface | SwiperElement | The <swiper> component provides a swiper container. |
| Interface | SwiperInterface | Provides an interface for sliding containers. |
| Interface | SwitchStyle | Defines the switch style. |
| Interface | SymbolGlyphInterface | Provides an interface for SymbolGlyph. |
| Interface | SymbolSpanInterface | Provides an interface for SymbolSpan. |
| Interface | TabBarIconStyle | TabBarIconStyle object. |
| Interface | TabContentAnimatedTransition | Defines the Tab Content animated transition options. |
| Interface | TabContentInterface | Provides an interface for switching the content view on a tab page. |
| Interface | TabContentTransitionProxy | The proxy of TabContentAnimatedTransition. |
| Interface | TabsAnimationEvent | Provides an interface for tabs animation. |
| Interface | TabsInterface | Provides an interface for switching views. |
| Interface | TabsOptions | Options used to create Tabs. |
| Interface | TapGestureEvent | Defines event info for tap gesture. |
| Interface | TapGestureHandlerOptions | Defines the TapGestureHandler options. |
| Interface | TapGestureInterface | Defines TapGesture interface extends GestureInterface<TapGestureInterface>. |
| Interface | TapGestureParameters | Defines TapGesture parameters. |
| Interface | TemplateOptions | Define a builder template option parameter. |
| Interface | TerminationInfo | Indicates the information when the provider of the embedded UI is terminated. |
| Interface | TextAreaElement | The <textarea> component provides an interactive interface to receive user input |
| Interface | TextAreaInterface | Provides an interface for the multi-line text input component. |
| Interface | TextAreaOptions | Defines the options of TextArea. |
| Interface | TextBackgroundStyle | Define the background style of span. |
| Interface | TextBaseController | Define the text selection controller. |
| Interface | TextCascadePickerRangeContent | Define the contents of text cascade picker. |
| Interface | TextChangeOptions | The TextChangeOptions. |
| Interface | TextClockConfiguration | TextClockConfiguration used by text clock content modifier |
| Interface | TextClockInterface | TextClock component, which provides the text clock capability. |
| Interface | TextContentControllerOptions | Defines the span options of TextContentController. |
| Interface | TextDataDetectorConfig | Text data detector config. |
| Interface | TextDecorationOptions | Defines the options of decoration. |
| Interface | TextEditControllerEx | Define the text extended editing controller. |
| Interface | TextInputInterface | Provides a single-line text input component interface. |
| Interface | TextInputOptions | Defines the options of TextInput. |
| Interface | TextInterface | Provides an interface for writing texts. |
| Interface | TextMenuItem | TextMenuItem |
| Interface | TextMetrics | TextMetrics |
| Interface | TextOptions | Defines the options of Text. |
| Interface | TextPickerDialogOptions | Defines the TextPickerDialogOptions for Text Picker Dialog. |
| Interface | TextPickerInterface | TextPickerInterface |
| Interface | TextPickerOptions | Defines the options of TextPicker. |
| Interface | TextPickerRangeContent | Define the contents of each selector item. |
| Interface | TextPickerResult | Defines the struct of TextPickerResult. |
| Interface | TextPickerTextStyle | Provide an interface for the text style of the text picker. |
| Interface | TextRange | Defines range of text type component. |
| Interface | TextStyle | Defines TextStyle in the AlertDialog. |
| Interface | TextStyleInterface | TextStyleInterface |
| Interface | TextTimerConfiguration | TextTimerConfiguration used by content modifier. |
| Interface | TextTimerInterface | Provides an interface for texttimer containers. |
| Interface | TextTimerOptions | Defines the options of TextTimer. |
| Interface | Theme | Defines the struct of Theme. |
| Interface | TimePickerDialogOptions | Defines the TimePickerDialogOptions for Data Picker Dialog. |
| Interface | TimePickerInterface | Defines the TimePicker Component. |
| Interface | TimePickerOptions | Defines the options of TimePicker. |
| Interface | TimePickerResult | Defines the struct of TimePickerResult. |
| Interface | TodayStyle | Non current day style. |
| Interface | ToggleConfiguration | ToggleConfiguration used by toggle Modifier |
| Interface | ToggleInterface | Defines the toggle interface. |
| Interface | ToolbarItem | Defines configurable parameters for toolbar item. |
| Interface | TouchEvent | Touch Action Function Parameters |
| Interface | TouchObject | Type of the touch event. |
| Interface | TouchPoint | Defines TouchPoint |
| Interface | TransformObject | TransformObject |
| Interface | TransitionOptions | Defines the param of transition. |
| Interface | TranslateOptions | Defines the options of translate. |
| Interface | TypeConstructor | Define TypeConstructor type. |
| Interface | TypeConstructorWithArgs | Define class constructor with arbitrary parameters. |
| Interface | TypedFrameNode | Used to define the FrameNode type. |
| Interface | UICommonEvent | Defines a UICommonEvent which is used to set different common event to target co |
| Interface | UIExtensionComponentInterface | Provide an interface for the UIExtensionComponent, which is used <br/>to render  |
| Interface | UIExtensionOptions | This interface is used to set the options for UIExtensionComponentAttribute duri |
| Interface | UIExtensionProxy | This interface is used for send data to the UIExtensionAbility.<br/> It is retur |
| Interface | UIGestureEvent | Defines a UIGestureEvent which is used to set different gestures to target compo |
| Interface | UnderlineColor | Defines the underline color width property. |
| Interface | Vector2 | Defined a vector with two values. |
| Interface | Vector2T | Defined a vector with two T type values. |
| Interface | Vector3 | Defined a vector with three values. |
| Interface | VideoElement | The <video> component provides a video player. |
| Interface | VideoInterface | Defines the video interface. |
| Interface | VideoOptions | Defines the video options. |
| Interface | ViewModel | View model |
| Interface | VirtualScrollOptions | Define the options of repeat virtualScroll to implement reuse and lazy loading. |
| Interface | VisibleAreaEventOptions | Defines the options about VisibleAreaEvent. |
| Interface | VisibleListContentInfo | Defines the visible list content info. |
| Interface | WaterFlowInterface | Defines the water flow interface. |
| Interface | WaterFlowOptions | Defines the water flow options. |
| Interface | WebElement | The <web> component is a container for displaying web page content. |
| Interface | WeekStyle | Week Style. |
| Interface | WindowAnimationTarget | Window animation target. |
| Interface | WindowSceneInterface | Defines the interface of WindowScene. |
| Interface | WithThemeOptions | Defines the struct of WithThemeOptions. |
| Interface | WorkStateStyle | Work state style. |
| Interface | XComponentInterface | Defines XComponent. |
| Interface | XComponentOptions | Defines the xcomponent options. |
| Interface | observer | Defines the observer interface. |
| Interface | sharedTransitionOptions | Defines the shard transition function params. |

#### @kit.AbilityKit (+153：Class 29 / Interface 121 / Enum 3)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | AbilityForegroundStateObserver | The ability foreground state observer. |
| Class | AbilityStageContext | The context of an abilityStage. It allows access to abilityStage-specific resour |
| Class | AbilityStartCallback | The callback of UIAbility or UIExtensionAbility. |
| Class | AbilityStateData | The ability or extension state data. |
| Class | AppForegroundStateObserver | The app foreground state observer. |
| Class | AppStateData | The application state data. |
| Class | ApplicationContext | The context of an application. It allows access to application-specific resource |
| Class | ApplicationStateObserver | The application state observer. |
| Class | AtomicServiceOptions | AtomicServiceOptions is the basic communication component of the system. |
| Class | AutoFillExtensionContext | The context of auto fill extension. It allows access to AutoFillExtension-specif |
| Class | BaseContext | The base context of 'app.Context' for FA Mode or 'application.Context' for Stage |
| Class | Context | The base context of an ability or an application. It allows access to applicatio |
| Class | EmbeddableUIAbility | class of embeddable UIAbility. |
| Class | EmbeddableUIAbilityContext | The context of an embeddable UIAbility. |
| Class | EmbeddedUIExtensionAbility | The class of embedded UI extension ability. |
| Class | ErrorObserver | The observer will be called by system when an error occurs. |
| Class | EventHub | The event center of a context, support the subscription and publication of event |
| Class | ExtensionContext | The context of an extension. It allows access to extension-specific resources. |
| Class | PermissionRequestResult | The result of requestPermissionsFromUser with asynchronous callback. |
| Class | PhotoEditorExtensionAbility | Class of the photo editor ExtensionAbility, which provides APIs for you to edit  |
| Class | PhotoEditorExtensionContext | The context of Photo Editor extension. It allows access to PhotoEditorExtension- |
| Class | ProcessData | The process data. |
| Class | ServiceExtensionContext | The context of service extension. It allows access to serviceExtension-specific  |
| Class | StartupConfigEntry | The configuration entry for running startup tasks. |
| Class | StartupListener | The listener for running startup tasks, which will be called when all tasks comp |
| Class | UIAbilityContext | The context of an ability. It allows access to ability-specific resources. |
| Class | UIExtensionContext | The context of UI extension. It allows access to UIExtension-specific resources. |
| Class | UIServiceExtensionAbility | The class of UI service extension ability. |
| Class | UIServiceExtensionContext | The context of UI service extension. It allows access to UIServiceExtension-spec |
| Enum | AutoFillType | Type of auto fill. |
| Enum | MultiAppMode | Type of app multi app mode. |
| Enum | PopupPlacement | Popup placement. |
| Interface | AbilityDelegator | A global test utility interface used for adding AbilityMonitor objects and contr |
| Interface | AbilityDelegatorArgs | Store unit testing-related parameters, including test case names, and test runne |
| Interface | AbilityFirstFrameStateData | The ability first frame state data. |
| Interface | AbilityFirstFrameStateObserver | The ability first frame state observer. |
| Interface | AbilityFormInfo | AbilityFormInfo: the form info of an ability. |
| Interface | AbilityInfo | Obtains configuration information about an ability |
| Interface | AbilityMonitor | Provide methods for matching monitored Ability objects that meet specified condi |
| Interface | AbilityResult |  |
| Interface | AbilityRunningInfo | The class of an ability running information. |
| Interface | AbilityStageMonitor | Provide methods for matching monitored AbilityStage objects that meet specified  |
| Interface | ApiVersion | ApiVersion: the bundle Api version class. |
| Interface | AppCloneIdentity | AppCloneIdentity contains BundleName and appIndex |
| Interface | AppProvisionInfo | Indicates the profile file information of a bundle. |
| Interface | AppVersionInfo | Defines an AppVersionInfo object. |
| Interface | ApplicationInfo | Obtains configuration information about an application |
| Interface | AutoFillPopupConfig | Auto Fill Popup config. |
| Interface | AutoFillRect | Auto fill rectangle. |
| Interface | AutoStartupCallback | The class of auto startup callback. |
| Interface | AutoStartupInfo | The class of auto startup info. |
| Interface | BundleConfigInfo | BundleConfigInfo: the bundle summary class. |
| Interface | BundleInfo | Obtains configuration information about a bundle |
| Interface | BundleInstaller | Offers install, upgrade, and remove bundles on the devices. |
| Interface | BundlePackInfo | The bundle pack info class. |
| Interface | BundleResourceInfo | Obtains resource information about a bundle |
| Interface | BundleStatusCallback | Contains basic Ability information, which uniquely identifies an launcher Status |
| Interface | BusinessAbilityInfo | Contains basic business ability information. |
| Interface | ChildProcessArgs | Define args to pass to child process. |
| Interface | ChildProcessOptions | Define options for starting child process. |
| Interface | ConnectOptions | As an input parameter when connecting a specified background service, it is used |
| Interface | Context | The context of an ability or an application.  It allows access to application-sp |
| Interface | ContinuableInfo | Continuable information corresponding to ability. |
| Interface | ContinuationExtraParams | Indicates the description of additional parameters for continuation. |
| Interface | ContinuationResult | Indicates the description of transfer results for continuation. |
| Interface | ContinueCallback | ContinueCallback registered for notify continue result. |
| Interface | ContinueDeviceInfo | Parameters corresponding to continue mission. |
| Interface | ContinueMissionInfo | Parameters corresponding to continue mission. |
| Interface | CustomData | User defined data. When the modal window of AutoFillExtension needs to be raised |
| Interface | CustomizeData | Indicates the custom metadata |
| Interface | DataAbilityHelper | DataAbilityHelper |
| Interface | DataAbilityOperation | Indicates an array of data operations that can contain several different operati |
| Interface | DataAbilityResult | Indicates the return result of the data to be manipulated. |
| Interface | DataItem | Indicates the data item defined in router item |
| Interface | Dependency | Indicates the dependency |
| Interface | DispatchInfo | Dispatch info related to free install |
| Interface | ElementName | Contains basic Ability information, which uniquely identifies an ability. You ca |
| Interface | ExtensionAbility | ExtensionAbility: the extension ability forms class. |
| Interface | ExtensionAbilityInfo | Extension information about a bundle |
| Interface | ExtensionRunningInfo | The class of an extension running information. |
| Interface | FillRequest | Fill request for automatic filling. |
| Interface | FillRequestCallback | Fill request callback for automatic filling. |
| Interface | FillResponse | Fill response for automatic filling. |
| Interface | HapModuleInfo | Obtains configuration information about a module. |
| Interface | InstallParam | Provides parameters required for installing or uninstalling an application. |
| Interface | InstallStatus | Indicates the install or uninstall status |
| Interface | LauncherAbilityInfo | Contains basic Ability information, which uniquely identifies an ability. You ca |
| Interface | LauncherAbilityResourceInfo | Obtains resource information about a launcher ability |
| Interface | LifecycleApp | interface of app lifecycle. |
| Interface | LifecycleData | interface of data lifecycle. |
| Interface | LifecycleForm | interface of form lifecycle. |
| Interface | LifecycleService | interface of service lifecycle. |
| Interface | LoopObserver | The observer will be called by system when application main thread loop execute  |
| Interface | Metadata | Indicates the Metadata |
| Interface | MissionCallback | MissionCallback registered by app. |
| Interface | MissionDeviceInfo | Parameters corresponding to mission. |
| Interface | MissionInfo | Mission information corresponding to ability. |
| Interface | MissionListener | MissionListener registered by app. |
| Interface | MissionParameter | Parameters corresponding to mission. |
| Interface | MissionSnapshot | Mission snapshot corresponding to mission. |
| Interface | ModuleAbilityInfo | ModuleAbilityInfo: the ability info of a module. |
| Interface | ModuleConfigInfo | ModuleConfigInfo: the module summary of a bundle. |
| Interface | ModuleDistroInfo | ModuleDistroInfo: the bundle info summary class. |
| Interface | ModuleInfo | Stores module information about an application. |
| Interface | ModuleMetadata | Indicates the ModuleMetadata |
| Interface | MultiAppMode | Indicates MultiAppMode |
| Interface | OpenLinkOptions | Define the available options for openLink API. |
| Interface | OverlayModuleInfo | Obtains configuration information about a overlay hap module. |
| Interface | PacMap | Defines a PacMap object for storing a series of values. |
| Interface | PackageConfig | PackageConfig: the package info class. |
| Interface | PackageSummary | PackageSummary: the package summary class. |
| Interface | PageNodeInfo | Page node info for automatic filling. |
| Interface | ParameterItem | Obtains information about the ability that a shortcut will start. |
| Interface | PermissionDef | Indicates the defined permission details in file config.json |
| Interface | PermissionOptions |  |
| Interface | PermissionRequestResult |  |
| Interface | PopupSize | Popup size. |
| Interface | PreinstalledApplicationInfo | Indicates the information of preinstalled application |
| Interface | PreloadItem | Indicates the preloadItem |
| Interface | ProcessInfo |  |
| Interface | ProcessInformation | The class of an process information. |
| Interface | ProcessRunningInfo | The class of an process running information. |
| Interface | RecoverableApplicationInfo | Indicates the RecoverableApplicationInfo |
| Interface | RemoteAbilityInfo | Contains basic remote ability information. |
| Interface | ReqPermissionDetail | Indicates the required permissions details defined in file config.json |
| Interface | RouterItem | Indicates the router item |
| Interface | RunningAppClone | The class of single running app information. |
| Interface | RunningMultiAppInfo | The class of running multi app information. |
| Interface | RunningMultiInstanceInfo | The class of app running instance information. |
| Interface | SaveRequest | Save request for automatic filling. |
| Interface | SaveRequestCallback | Save request callback for automatic filling. |
| Interface | SharedBundleInfo | Provides information about a shared bundle. |
| Interface | SharedModuleInfo | Indicates the shared module info. |
| Interface | ShellCmdResult | A object that records the result of shell command executes. |
| Interface | ShortcutInfo | Provides information about a shortcut, including the shortcut ID and label. |
| Interface | ShortcutWant | Provides methods for obtaining information about the ability that a shortcut wil |
| Interface | SignatureInfo | Indicates SignatureInfo |
| Interface | Skill | Obtains configuration information about an skill |
| Interface | SkillUri | Obtains configuration information about an skillUri |
| Interface | StartAbilityParameter | Define startup Ability parameters, which can be used as input parameters. |
| Interface | StartupConfig | The interface of configuration for running startup tasks. |
| Interface | TriggerInfo | Provides the information required for triggering a WantAgent. |
| Interface | UIServiceExtensionConnectCallback | UI service extension connect callback. |
| Interface | UIServiceHostProxy | UI service host proxy. |
| Interface | UIServiceProxy | UI service proxy. |
| Interface | UpdateRequest | Update request for automatic filling. |
| Interface | UsedScene | The scene which is used |
| Interface | Validity | The validity of the profile file. |
| Interface | Version | Version: the bundle version class. |
| Interface | ViewData | View data for automatic filling. |
| Interface | Want | Want is the basic communication component of the system. |
| Interface | WantAgentInfo | Provides the information required for triggering a WantAgent. |
| Interface | WindowSize | Indicates the window size. |

#### @kit.ArkWeb (+111：Class 23 / Interface 61 / Enum 27)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | ClientAuthenticationHandler | Defines the client certificate request result, related to {@link onClientAuthent |
| Class | ConsoleMessage | Encompassed message information as parameters to {@link onConsole} method. |
| Class | ControllerHandler | Defines the onWindowNew callback, related to {@link onWindowNew} method. |
| Class | DataResubmissionHandler | Defines the onDataResubmission callback, related to {@link onDataResubmission} m |
| Class | EventResult | Defines the touch event result. |
| Class | FileSelectorParam | Encompassed message information as parameters to {@link onFileSelectorShow} meth |
| Class | FileSelectorResult | Defines the file selector result, related to {@link onFileSelectorShow} method. |
| Class | FullScreenExitHandler | Define the handler to exit the full screen mode, related to the {@link onFullScr |
| Class | HttpAuthHandler | Defines the http auth request result, related to {@link onHttpAuthRequest} metho |
| Class | JsGeolocation | Defines the js geolocation request. |
| Class | JsResult | Defines the js result. |
| Class | PermissionRequest | Defines the onPermissionRequest callback, related to {@link onPermissionRequest} |
| Class | ScreenCaptureHandler | Defines the onScreenCapture callback, related to {@link onScreenCapture} method. |
| Class | SslErrorHandler | Defines the ssl error request result, related to {@link onSslErrorEventReceive}  |
| Class | WebAttribute | Defines the Web attribute functions. |
| Class | WebContextMenuParam | Defines the context menu param, related to {@link WebContextMenuParam} method. |
| Class | WebContextMenuResult | Defines the context menu result, related to {@link WebContextMenuResult} method. |
| Class | WebController | Defines the Web controller. |
| Class | WebCookie | Defines the Web cookie. |
| Class | WebKeyboardController | Define the controller to interact with a custom keyboard, related to the {@link  |
| Class | WebResourceError | Defines the Web resource error. |
| Class | WebResourceRequest | Defines the Web resource request. |
| Class | WebResourceResponse | Defines the Web resource response. |
| Enum | BlurOnKeyboardHideMode | Enum type supplied to {@link blurOnKeyboardHideMode} for setting the web blurOnK |
| Enum | CacheMode | Enum type supplied to {@link cacheMode} for setting the Web cache mode. |
| Enum | ContextMenuEditStateFlags | Defines the context menu supported event bit flags, related to {@link onContextM |
| Enum | ContextMenuInputFieldType | Defines the context menu input field type, related to {@link onContextMenuShow}  |
| Enum | ContextMenuMediaType | Defines the context menu media type, related to {@link onContextMenuShow} method |
| Enum | ContextMenuSourceType | Defines the context menu source type, related to {@link onContextMenuShow} metho |
| Enum | FileSelectorMode | Enum type supplied to {@link FileSelectorParam} when onFileSelectorShow being ca |
| Enum | HitTestType | Enum type supplied to {@link getHitTest} for indicating the cursor node HitTest. |
| Enum | MessageLevel | Enum type supplied to {@link getMessageLevel} for receiving the console log leve |
| Enum | MixedMode | The Web's behavior to load from HTTP or HTTPS. Defaults to MixedMode.None. |
| Enum | NativeEmbedStatus | Defines the embed status, related to {@link NativeEmbedDataInfo}. |
| Enum | OverScrollMode | Enum type supplied to {@link overScrollMode} for setting the web overScroll mode |
| Enum | ProtectedResourceType | Defines the accessible resource type, related to {@link onPermissionRequest} met |
| Enum | RenderExitReason | Enum type supplied to {@link renderExitReason} when onRenderExited being called. |
| Enum | RenderMode | Defines the web render mode, related to {@link RenderMode}. |
| Enum | RenderProcessNotRespondingReason | Enum type supplied to {@link RenderProcessNotRespondingData} when onRenderProces |
| Enum | SslError | Enum type supplied to {@link error} when onSslErrorEventReceive being called. |
| Enum | ThreatType | Enum type supplied to {@link threatType} for the website's threat type. |
| Enum | ViewportFit | Defines the viewport-fit type, related to {@link ViewportFit}. |
| Enum | WebCaptureMode | Enum type supplied to {@link captureMode} for setting the web capture mode. |
| Enum | WebDarkMode | Enum type supplied to {@link darkMode} for setting the web dark mode. |
| Enum | WebElementType | Defines Web Elements type. |
| Enum | WebKeyboardAvoidMode | Enum type supplied to {@link keyboardAvoidMode} for setting the web keyboard avo |
| Enum | WebLayoutMode | Enum type supplied to {@link layoutMode} for setting the web layout mode. |
| Enum | WebNavigationType | Enum type supplied to {@link navigationType} for the navigation's type. |
| Enum | WebNetErrorList | Web net error list. |
| Enum | WebResponseType | ResponseType for contextMenu |
| Interface | AdsBlockedDetails | Defines the ads block details. |
| Interface | ExpandedMenuItemOptions | Defines the menu item option. |
| Interface | FirstMeaningfulPaint | Defines the first content paint rendering of web page. |
| Interface | FullScreenEnterEvent | Defines the event details when the web component enter full screen mode. |
| Interface | Header | Defines the Web's request/response header. |
| Interface | IntelligentTrackingPreventionDetails | Defines the Intelligent Tracking Prevention details. |
| Interface | JavaScriptProxy | Defines the JavaScript object to be injected. |
| Interface | LargestContentfulPaint | Defines the largest content paint rendering of web page. |
| Interface | LoadCommittedDetails | Defines the load committed details. |
| Interface | NativeEmbedDataInfo | Defines the Embed Data info. |
| Interface | NativeEmbedInfo | Defines the embed info. |
| Interface | NativeEmbedTouchInfo | Defines the user touch info. |
| Interface | NativeEmbedVisibilityInfo | Defines the Embed Visibility info. |
| Interface | NativeMediaPlayerConfig | The configuration of native media player. |
| Interface | NestedScrollOptionsExt | Define nested scroll options |
| Interface | OnAlertEvent | Defines the triggered function when the web page wants to display a JavaScript a |
| Interface | OnAudioStateChangedEvent | Defines the playing state of audio on web page. |
| Interface | OnBeforeUnloadEvent | Defines the triggered function when the web page wants to confirm navigation fro |
| Interface | OnClientAuthenticationEvent | Defines the triggered callback when needs ssl client certificate from the user. |
| Interface | OnConfirmEvent | Defines the triggered function when the web page wants to display a JavaScript c |
| Interface | OnConsoleEvent | Defines the triggered function when the web page receives a JavaScript console m |
| Interface | OnContextMenuShowEvent | Defines the triggered callback when called to allow custom display of the contex |
| Interface | OnDataResubmittedEvent | Defines the triggered callback to decision whether resend form data or not. |
| Interface | OnDownloadStartEvent | Defines the triggered function when starting to download. |
| Interface | OnErrorReceiveEvent | Defines the triggered function when the web page receives a web resource loading |
| Interface | OnFaviconReceivedEvent | Defines the triggered callback when the application receive a new favicon for th |
| Interface | OnFirstContentfulPaintEvent | Defines triggered when the first content rendering of web page. |
| Interface | OnGeolocationShowEvent | Defines the triggered function when requesting to show the geolocation permissio |
| Interface | OnHttpAuthRequestEvent | Defines the triggered when the browser needs credentials from the user. |
| Interface | OnHttpErrorReceiveEvent | Defines the triggered function when the web page receives a web resource loading |
| Interface | OnInterceptRequestEvent | Defines the triggered callback when the resources loading is intercepted. |
| Interface | OnLoadInterceptEvent | Defines the triggered callback when the resources loading is intercepted. |
| Interface | OnOverScrollEvent | Defines the function Triggered when the over scrolling. |
| Interface | OnPageBeginEvent | Defines the triggered function at the begin of web page loading. |
| Interface | OnPageEndEvent | Defines the triggered function at the end of web page loading. |
| Interface | OnPageVisibleEvent | Defines the triggered callback when previous page will no longer be drawn and ne |
| Interface | OnPermissionRequestEvent | Defines the triggered callback when the host application that web content from t |
| Interface | OnProgressChangeEvent | Defines the triggered function when the page loading progress changes. |
| Interface | OnPromptEvent | Defines the triggered function when the web page wants to display a JavaScript p |
| Interface | OnRefreshAccessedHistoryEvent | Defines the triggered callback when the Web page refreshes accessed history. |
| Interface | OnRenderExitedEvent | Defines the triggered when the render process exits. |
| Interface | OnResourceLoadEvent | Defines the triggered when the url loading. |
| Interface | OnScaleChangeEvent | Defines the triggered when the scale of WebView changed. |
| Interface | OnScreenCaptureRequestEvent | Defines the triggered callback when the host application that web content from t |
| Interface | OnScrollEvent | Defines function Triggered when the scroll bar slides to the specified position. |
| Interface | OnSearchResultReceiveEvent | Defines function Triggered when the host application call searchAllAsync. |
| Interface | OnShowFileSelectorEvent | Defines the triggered when the file selector shows. |
| Interface | OnSslErrorEventReceiveEvent | Defines the triggered callback when the Web page receives an ssl Error. |
| Interface | OnTitleReceiveEvent | Defines the triggered function when the title of the main application document c |
| Interface | OnTouchIconUrlReceivedEvent | Defines the triggered callback when the application receive an new url of an app |
| Interface | OnWindowNewEvent | Defines the triggered callback when web page requires the user to create a windo |
| Interface | RenderProcessNotRespondingData | Defines the render process not responding info. |
| Interface | ScreenCaptureConfig | Defines the screen capture configuration. |
| Interface | ScriptItem | Defines the contents of the JavaScript to be injected. |
| Interface | SelectionMenuOptionsExt | Defines the selection menu options. |
| Interface | SslErrorEvent | Defines the ssl error event. |
| Interface | WebInterface | Defines the Web interface. |
| Interface | WebKeyboardCallbackInfo | Defines the web keyboard callback info related to the {@link onInterceptKeyboard |
| Interface | WebKeyboardOptions | Defines the web keyboard options when onInterceptKeyboardAttach event return. |
| Interface | WebMediaOptions | Defines the Media Options. |
| Interface | WebOptions | Defines the Web options. |

#### 未知模块 (+81：Class 9 / Interface 33 / Enum 39)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Duplex | Duplex streams are streams that implement both the Readable streams and Writable |
| Class | HashStream | Hash Stream. |
| Class | Readable | The stream from which data can be read. |
| Class | RunningLock | Provides a mechanism to prevent the system from hibernating so that the applicat |
| Class | Transform | Transform stream is a Duplex stream where the output is computed in some way fro |
| Class | UnifiedDataProperties | Describe the unified data properties. |
| Class | Writable | Streams to which data can be written. |
| Class | unnamed | Java class. |
| Class | unnamed | Obtains the classification of this notification. |
| Enum | AddressFamily | Enum for Address Family |
| Enum | BigIntMode | Enum defining modes for handling bigint. |
| Enum | CapturerChannel | Enumerates capturer channel. |
| Enum | CertificateDialogErrorCode | Enum for result code |
| Enum | CompressFlushMode | CompressFlushMode |
| Enum | CompressMethod | The deflate compression method (the only one supported in this version). |
| Enum | ControlObject | Describes the control object. |
| Enum | ControlType | Describes the control type. |
| Enum | ControlTypeValue | Describes the control type value. |
| Enum | DataType | Enumerates the types of data under lock screen. |
| Enum | DeviceChargeState | Enum for the charge state. |
| Enum | DeviceType | Enum for the custom type of remote device. |
| Enum | DisconnectCause | Enum for cause of disconnect. |
| Enum | DynamicRangeType | Enumeration of dynamic range type |
| Enum | EvaluationResultCode | Enumerates evaluation result code. |
| Enum | FirewallRuleAction | Firewall rule behavior enumeration. |
| Enum | FoldState | Define the folding state of wallpaper |
| Enum | GestureType | Creating an Object |
| Enum | HapticFeedback | Simple and universal vibration effects. |
| Enum | NetFirewallOrderField | Pagination query sorting field. |
| Enum | NetFirewallOrderType | Pagination query sorting type. |
| Enum | NetFirewallRuleDirection | Firewall rule direction enumeration. |
| Enum | NetFirewallRuleType | Indicates the firewall rule type. |
| Enum | OffsetReferencePoint | Define the reference point for offset. |
| Enum | OperatingHandStatus | Enum for operating hand status. |
| Enum | OperationType | An enum type indicates the additional action to be performed during operation. |
| Enum | PathDirection | Enumerates direction for adding closed contours. |
| Enum | Pattern | Enumerates the patterns allowed in the system pasteboard. |
| Enum | PolicyType | Enumerates type. |
| Enum | ReturnStatus | Return codes for the compression/decompression functions. |
| Enum | RotateState | Define the rotation state of wallpaper |
| Enum | ShareOptions | Types of scope that UnifiedData can be used. |
| Enum | SystemLoadLevel | Enumerates the {@link SystemLoadLevel} types. |
| Enum | TextAlign | Refers to how to align the horizontal position of text when displaying text. |
| Enum | ThumbnailVisibility | Ability to access thumbnail |
| Enum | TraceFlag | Enum for trace flag |
| Enum | UnbondCause | Enum for cause of unbond. |
| Enum | UploadFileType | Enumerates upload file type. |
| Enum | VolumeFlag | Enumerates volume related operations. Flags should be powers of 2! |
| Interface | BatteryInfo | Describes the contents of the battery information. |
| Interface | CertBlob | User certificate data. |
| Interface | ContinuousTaskCancelInfo | The continuous task cancel info. |
| Interface | ContinuousTaskNotification | The info of continuous task notification. |
| Interface | ControlDeviceActionParams | Describes information about controlling the Bluetooth peripheral. |
| Interface | DecodeToStringOptions | Defines the decode with stream related options parameters. |
| Interface | DiscoveryResult | Describes the contents of the discovery results |
| Interface | EvaluationResult | Describes evaluation result. |
| Interface | Filter | The Filter for Component. |
| Interface | InfraredFrequency | Infrared frequency range supported by the IR emitter. |
| Interface | MediaKeySystemDescription | Name and UUID of DRM plugin. |
| Interface | MemoryLimit | Application process memory limit |
| Interface | ModelConfig | Manages configurations of the embedding model. |
| Interface | NativeMemInfo | Application process native memory information. |
| Interface | NetFirewallPolicy | Firewall policy. |
| Interface | ParseOptions | Parse's options |
| Interface | PickInfo | Describes the region of the screen to pick info. |
| Interface | PlainText | Describe the plain text uniform data struct. |
| Interface | Point | Coordinates in the font layout. |
| Interface | ReadableOptions | Return readable options. |
| Interface | SecurityEvent | Provides the SecurityEvent type, including the event id, version info, report co |
| Interface | SnapshotRegion | Defines the extra options for snapshot taking. |
| Interface | Storage | Provides interfaces to obtain and modify storage data. <p>The storage data is st |
| Interface | SystemMemInfo | System memory information |
| Interface | ThreadCpuUsage | Application CPU usage of thread. |
| Interface | TrustedPairedDevice | Describes device of cloud pair. |
| Interface | TrustedPairedDevices | Describes the cloud pair device. |
| Interface | UploadFile | Describes upload file information. |
| Interface | VMMemoryInfo | The memory information of application virtual machine. |
| Interface | WakeupManager | Implements wakeup management. |
| Interface | WakeupSourceFile | Describes wakeup source file information. |
| Interface | WallpaperInfo | WallpaperInfo definition including folding status, rotation status, and resource |
| Interface | WindowProxy | The proxy of the UIExtension window. |

#### @kit.ArkGraphics3D (+37：Class 1 / Interface 30 / Enum 6)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Scene | Defines the 3d scene. |
| Enum | EnvironmentBackgroundType | The enum of environment background type. |
| Enum | LightType | The enum of light type. |
| Enum | MaterialType | The enum of material type. |
| Enum | NodeType | The enum of node type. |
| Enum | SceneResourceType | The enum of SceneResource type. |
| Enum | ToneMappingType | The enum of tone mapping type. |
| Interface | Aabb | Axis aligned bounding box. |
| Interface | Animation | Animation resource. |
| Interface | Camera | Defines camera. |
| Interface | Color | Defines Color. |
| Interface | Container | Defines a scene object container. |
| Interface | DirectionalLight | Defines directional light. |
| Interface | Environment | Environment resource. |
| Interface | Geometry | Defines Geometry interface. |
| Interface | Image | Image resource. |
| Interface | LayerMask | Defines the layer mask of the node. |
| Interface | Light | Defines light interface. |
| Interface | Material | Material resource. |
| Interface | Mesh | Mesh resource. |
| Interface | Node | Defines Node interface. |
| Interface | PostProcessSettings | Defines post processing settings. |
| Interface | Quaternion | Quaternion representing a rotation. |
| Interface | Rect | Defines rectangle. |
| Interface | RenderParameters | Defines parameters for manual rendering. |
| Interface | SceneNodeParameters | The scene node parameters type. |
| Interface | SceneResource | Define scene resource extended by other 3d resource. |
| Interface | SceneResourceFactory | The scene resource factory. |
| Interface | SceneResourceParameters | The scene resource parameters type. |
| Interface | Shader | Shader resource. |
| Interface | ShaderMaterial | Shader material resource. |
| Interface | SpotLight | Defines spot light. |
| Interface | SubMesh | Sub mesh resource. |
| Interface | ToneMappingSettings | Defines tone mapping parameters. |
| Interface | Vec2 | Defines Vec2. |
| Interface | Vec3 | Defines Vec3. |
| Interface | Vec4 | Defines Vec4. |

#### @kit.NotificationKit (+32：Class 0 / Interface 30 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | LiveViewStatus | Enum for live view notification option type. |
| Enum | NotificationFlagStatus | The status of the notification flag. |
| Interface | BadgeEnabledChangedCallback | Defines the callback of BadgeEnabledChanged. |
| Interface | BadgeNumberCallbackData | Describes the badge number of the application has changed. |
| Interface | BundleOption | Describes a BundleOption. |
| Interface | DistributedOptions | Describes distributed options. |
| Interface | EnabledNotificationCallbackData | Describes the properties of the application that the permission to send notifica |
| Interface | NotificationActionButton | Describes an action button displayed in a notification. |
| Interface | NotificationBasicContent | Describes a normal text notification. |
| Interface | NotificationButton | Describes a system live view button type. |
| Interface | NotificationCapsule | Describes a system live view capsule type. |
| Interface | NotificationCheckRequest | Describes notification check information. |
| Interface | NotificationContent | Describes notification types. |
| Interface | NotificationFilter | Describes notification filter. |
| Interface | NotificationFlags | Describes a NotificationFlags instance. |
| Interface | NotificationLiveViewContent | Describes a live view notification. |
| Interface | NotificationLongTextContent | Describes a long text notification. |
| Interface | NotificationMultiLineContent | Describes a multi-line text notification. |
| Interface | NotificationPictureContent | Describes a picture-attached notification. |
| Interface | NotificationProgress | Describes a system live view progress type. |
| Interface | NotificationRequest | Defines a NotificationRequest instance. |
| Interface | NotificationSlot | Describes a NotificationSlot instance. |
| Interface | NotificationSorting | Provides sorting information about an active notification. |
| Interface | NotificationSortingMap | Provides sorting information about the active notifications among all the notifi |
| Interface | NotificationSubscribeInfo | Sets filter criteria of publishers for subscribing to desired notifications. |
| Interface | NotificationSubscriber | Provides methods that will be called back when the subscriber receives a new not |
| Interface | NotificationSystemLiveViewContent | Describes a system live view notification. |
| Interface | NotificationTemplate | Describes a NotificationTemplate instance. |
| Interface | NotificationTime | Describes a system live view time type. |
| Interface | NotificationUserInput | Describes a NotificationUserInput instance. |
| Interface | SubscribeCallbackData | Provides methods that will be called back when the subscriber receives a new not |
| Interface | UnifiedGroupInfo | Unified aggregation of information across applications. |

#### @kit.ConnectivityKit (+11：Class 0 / Interface 11 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | IsoDepTag | Provides methods for accessing IsoDep tag. |
| Interface | MifareClassicTag | Provides methods for accessing MifareClassic tag. |
| Interface | MifareUltralightTag | Provides methods for accessing MifareUltralight tag. |
| Interface | NdefFormatableTag | Provides methods for accessing NdefFormatable tag. |
| Interface | NdefMessage | Provides methods for Message of NDEF. |
| Interface | NdefTag | Provides methods for accessing NDEF tag. |
| Interface | NfcATag | Provides interfaces to control the read and write of tags that support the NFC-A |
| Interface | NfcBTag | Provides interfaces to create an {@code NfcBTag} and perform I/O operations on t |
| Interface | NfcFTag | Provides methods for creating an NFC-F tag, obtaining tag information, and contr |
| Interface | NfcVTag | Provides methods for creating an NFC-V tag, obtaining tag information, and contr |
| Interface | TagSession | Controls tag read and write. <p>Classes for different types of tags inherit from |

#### @kit.CoreFileKit (+11：Class 5 / Interface 4 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | AtomicFile | The AtomicFile class provides methods for performing atomic operations on files. |
| Class | BackupExtensionContext | The context of an ability or an application. It allows access to application-spe |
| Class | ReadStream | File Read Stream. |
| Class | TaskSignal | Task signal. |
| Class | WriteStream | File Write Stream. |
| Enum | AccessFlagType | Enumeration of different types of access flag. |
| Enum | AccessModeType | Enumeration of different types of access mode. |
| Interface | DfsListeners | The listeners of Distributed File System. |
| Interface | RandomAccessFileOptions | RandomAccessFileOptions type |
| Interface | ReadStreamOptions | ReadStreamOptions type |
| Interface | WriteStreamOptions | WriteStreamOptions type |

#### @kit.MediaLibraryKit (+6：Class 2 / Interface 2 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | MovingPhotoViewAttribute | Defines the moving photo view attribute functions. |
| Class | MovingPhotoViewController | Defines the MovingPhotoView controller. |
| Enum | DynamicRangeMode | Dynamic range mode of moving photo. |
| Enum | PixelMapFormat | Enumerates pixel map formats. |
| Interface | MovingPhotoViewInterface | Defines the moving photo view interface. |
| Interface | MovingPhotoViewOptions | Defines the moving photo view options. |

#### @kit.BasicServicesKit (+5：Class 0 / Interface 5 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | CommonEventData | the data of the commonEvent |
| Interface | CommonEventPublishData | containing the common event content and attributes |
| Interface | CommonEventSubscribeInfo | the information of the subscriber |
| Interface | CommonEventSubscriber | the subscriber of common event |
| Interface | GetDeviceOptions |  |

#### @kit.AccessibilityKit (+4：Class 1 / Interface 3 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | AccessibilityExtensionContext | The accessibility extension context. Used to configure, query information, and i |
| Interface | AccessibilityElement | Indicates an accessibility element. Supports querying element attributes, reques |
| Interface | ElementAttributeValues | Indicates the possible attributes of the element and the type of the attribute v |
| Interface | Rect | Indicates rectangle. |

#### @kit.AudioKit (+4：Class 0 / Interface 4 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | RingtoneOptions | Interface for ringtone options. |
| Interface | RingtonePlayer | Ringtone player object. |
| Interface | SystemToneOptions | System tone options used when SystemTonePlayer start playing. |
| Interface | SystemTonePlayer | System tone player object. |

#### @kit.AVSessionKit (+3：Class 1 / Interface 0 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | MediaControlExtensionContext | The context of media control extension. It allows access to UIExtension-specific |
| Enum | AVCastPickerColorMode | Definition of color mode of picker |
| Enum | AVCastPickerStyle | Definition of av cast picker style |

#### @kit.InputKit (+3：Class 0 / Interface 2 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | FingerprintAction | Enumerates fingerprint key event types. |
| Interface | FingerprintEvent | Fingerprint key event. |
| Interface | SwipeInward | Swipe Inward event on touchPad |

#### @kit.LocalizationKit (+2：Class 0 / Interface 2 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | RawFileDescriptor | Contains rawFile descriptor information. |
| Interface | Resource | Contains resource descriptor information. |

#### @kit.LocationKit (+2：Class 2 / Interface 0 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | FenceExtensionAbility | Class of fence extension ability. |
| Class | FenceExtensionContext | class of static subscriber extension context. |

#### @kit.MediaKit (+2：Class 0 / Interface 2 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | PlayParameters | Interface for play parameters. |
| Interface | SoundPool | Interface for soundPool instance. Manages and plays sound. Before calling an Sou |

#### @kit.AdsKit (+1：Class 0 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | Advertisement | Defines the advertisement data model. |

#### @kit.ArkData (+1：Class 0 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | ResultSet | Provides methods for accessing a database result set generated by querying the d |

#### @kit.ArkGraphics2D (+1：Class 0 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | BrightnessBlenderParam | The parameters of brightness blender. |

#### @kit.BackgroundTasksKit (+1：Class 1 / Interface 0 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | WorkSchedulerExtensionContext | The context of work scheduler extension. It allows access to WorkSchedulerExtens |

#### @kit.DriverDevelopmentKit (+1：Class 1 / Interface 0 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | DriverExtensionContext | The context of driver extension. It allows access to driverExtension-specific re |

#### @kit.FormKit (+1：Class 1 / Interface 0 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | FormExtensionContext | The context of form extension. It allows access to formExtension-specific resour |

#### @kit.NetworkKit (+1：Class 1 / Interface 0 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | VpnExtensionContext | The context of vpn extension. It allows access to serviceExtension-specific reso |

### 2.3 删除类/接口/枚举（按模块）

#### 未知模块 (-44)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | ApplicationDefinedRecord | Describe application defined data(this kind of data is provided and bound to Ope |
| Class | Audio | Describe the unified audio data |
| Class | CloudFileCache | CloudFileCache object. |
| Class | Download | Download object. |
| Class | File | Describe the unified file data |
| Class | FileSync | FileSync object. |
| Class | Folder | Describe the unified folder data |
| Class | GallerySync | GallerySync object. |
| Class | HTML | Describe the unified html data |
| Class | Hyperlink | Describe the unified link data |
| Class | Image | Describe the unified image data |
| Class | Path | Describes a path object. |
| Class | PlainText | Describe the unified plain text data |
| Class | Summary | The data abstract supported by unified data |
| Class | SystemDefinedAppItem | Describe system defined app item data(this kind of data is provided and bound to |
| Class | SystemDefinedForm | Describe system defined form data(this kind of data is provided and bound to Ope |
| Class | SystemDefinedPixelMap | Describe system defined pixel map data(this kind of data is provided and bound t |
| Class | SystemDefinedRecord | Describe system defined type data(this kind of data is provided and bound to Ope |
| Class | Text | Describe the unified text data |
| Class | UnifiedData | Describe the unified data. |
| Class | UnifiedRecord | Describe the unified record |
| Class | Video | Describe the unified video data |
| Enum | AbilityFlag | Used to query the enumeration value of abilityInfo. Multiple values can be passe |
| Enum | Action | the constant for action of the want |
| Enum | ApplicationFlag | Used to query the enumeration value of applicationInfo. Multiple values can be p |
| Enum | BackgroundMode | Supported background mode. |
| Enum | DeviceAddressType | Wi-Fi device address( mac / bssid ) type. |
| Enum | DownloadErrorType | Describes the download Error type. |
| Enum | ExtensionAbilityFlag | Used to query the enumeration value of ExtensionAbilityInfo. Multiple values can |
| Enum | ExtensionAbilityType | This enumeration value is used to identify various types of extension ability |
| Enum | Intention | Describe the sharing channel that UDMF support |
| Enum | MediaType | Enumeration types for different kind of Media Files |
| Enum | State | Describes the State type of download. |
| Enum | VibratorStopMode | Vibrator vibration stop mode. |
| Interface | DownloadProgress | The DownloadProgress data structure. |
| Interface | ExpandOption | The parameter of making expand screen |
| Interface | FileAsset | Provides methods to encapsulate file attributes. |
| Interface | HttpRequestOptions | Specifies the type and value range of the optional parameters in the HTTP reques |
| Interface | MediaAssetOption | Describes media resource options. |
| Interface | MediaSelectOption | Describes media selection options. |
| Interface | Options | Defines compress or decompress options. |
| Interface | Rect | Describes the region of the screen to capture. |
| Interface | ReverseGeocodingMockInfo | Configuration parameters for simulating reverse geocoding. |
| Interface | SyncProgress | The SyncProgress data structure. |

#### @kit.CoreFileKit (-20)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | File |  |
| Interface | Dir | Dir |
| Interface | Dirent | Dirent |
| Interface | FileAccessOption |  |
| Interface | FileCopyOption |  |
| Interface | FileDeleteOption |  |
| Interface | FileGetOption |  |
| Interface | FileListOption |  |
| Interface | FileListResponse |  |
| Interface | FileMkdirOption |  |
| Interface | FileMoveOption |  |
| Interface | FileReadArrayBufferOption |  |
| Interface | FileReadArrayBufferResponse |  |
| Interface | FileReadTextOption |  |
| Interface | FileReadTextResponse |  |
| Interface | FileResponse |  |
| Interface | FileRmdirOption |  |
| Interface | FileWriteArrayBufferOption |  |
| Interface | FileWriteTextOption |  |
| Interface | ReadOut | ReadOut |

### 2.4 方法/属性变化

| 类型 | 模块 | 变化量 |
|------|------|--------|
| +Property | 未知模块 | +3096 |
| +Method | 未知模块 | +2753 |
| +Method | @kit.ArkUI | +49 |
| +Property | @kit.ArkUI | +13 |
| +Method | @kit.AbilityKit | +2 |
| +Method | @kit.CoreFileKit | +2 |
| +Property | @kit.AbilityKit | +2 |
| -Method | 未知模块 | -197 |
| -Property | 未知模块 | -170 |
| -Method | @kit.CoreFileKit | -20 |

## 二、5.0 → 5.1（增量更新——圆弧手表适配）

### 2.1 总览

| 维度 | 新增 | 删除 | 净变化 |
|------|------|------|--------|
| 类/接口/枚举 | +158 | -6 | +152 |
| 方法/属性 | +642 | -22 | +620 |

### 2.2 新增类/接口/枚举（按模块）

#### @kit.ArkUI (+109：Class 19 / Interface 75 / Enum 15)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | ActionSheet | Declare the ActionSheet |
| Class | ArcAlphabetIndexerAttribute | Defines the arc alphabet index bar attribute functions. |
| Class | ArcDotIndicator | Define ArcDotIndicator, the indicator type is arc dot. |
| Class | ArcListAttribute | Defines the arc list attribute functions. |
| Class | ArcListItemAttribute | Defines the arc list item attribute functions. |
| Class | ArcScrollBarAttribute | Defines the arc scroll bar attribute functions. |
| Class | ArcSwiperAttribute | Defines the Arc swiper attribute functions. |
| Class | ArcSwiperController | Provide methods for controlling ArcSwiper component. |
| Class | BaseCustomComponent | Custom Component base class and it is migrated from class CustomComponent. |
| Class | ConnectOptions | Define  ConnectOptions class. |
| Class | CustomComponentV2 | Custom ComponentV2 |
| Class | LevelOrder | Defines level order. |
| Class | LongPressRecognizer | Defines the long press gesture recognizer. |
| Class | PinchRecognizer | Defines the pinch gesture recognizer. |
| Class | RotationRecognizer | Defines the rotation gesture recognizer. |
| Class | SimpleAnimatorOptions | Defines the SimpleAnimatorOptions class. |
| Class | SwipeRecognizer | Defines the swipe gesture recognizer. |
| Class | TapRecognizer | Defines the tap gesture recognizer. |
| Class | TextMenuController | class TextMenuController |
| Enum | AccessibilityRoleType | Enum for accessibility component type |
| Enum | AccessibilitySamePageMode | Defines the same page mode |
| Enum | ArcDirection | Declare the direction of arc indicator. |
| Enum | AxisAction | Type of axis action. |
| Enum | CrownAction | Rotating crown event behavior. |
| Enum | CrownSensitivity | Sensitivity of rotating crown. |
| Enum | DatePickerMode | Defines the mode of the date picker. |
| Enum | EffectEdge | Enumerates the effective edge of the edge effect. |
| Enum | HapticFeedbackMode | Defines the menu haptic feedback mode. |
| Enum | MarqueeStartPolicy | Defines marquee start policy. |
| Enum | MarqueeState | Defines marquee state. |
| Enum | NavDestinationActiveReason | Reason of navDestination be active or inactive. |
| Enum | PixelRoundMode | Pixel Round Mode |
| Enum | TextMenuShowMode | Defines text menu show mode. |
| Enum | WindowModeFollowStrategy | Enumeration of different types of WindowModeFollowStrategy. |
| Interface | AccelerationOptions | Defines acceleration options. |
| Interface | ActionSheetButtonOptions | Base button params used for ActionSheet. |
| Interface | ActionSheetOffset | ActionSheet offset. |
| Interface | ActionSheetOptions | The options of ActionSheet. |
| Interface | AlertDialogButtonBaseOptions | Base button param. |
| Interface | AlphabetIndexerOptions | AlphabetIndexer constructor options. |
| Interface | ArcAlphabetIndexerInitInfo | Define the initialization parameters of the arc alphabet index bar |
| Interface | ArcAlphabetIndexerInterface | Arc Alphabet index bar. |
| Interface | ArcListInterface | Defines the arc list component. |
| Interface | ArcListItemInterface | Defines the arc list item component. |
| Interface | ArcScrollBarInterface | Defines the arc scroll bar component. |
| Interface | ArcScrollBarOptions | Defines the arc scroll bar options. |
| Interface | ArcSwiperInterface | Provide an interface for ArcSwiper. |
| Interface | ArkListOptions | Defines the arc list options. |
| Interface | AutoPlayOptions | Define autoPlay related options. |
| Interface | AxisEvent | The axis event triggers this method invocation. |
| Interface | BackgroundImageOptions | Define the options for background image. |
| Interface | ButtonIconOptions | ButtonStyle icons. |
| Interface | ColorStop | ColorStop type |
| Interface | ColumnOptions | Column constructor options. |
| Interface | ColumnOptionsV2 | Column constructor options. |
| Interface | CrownEvent | CrownEvent object description |
| Interface | EllipseOptions | Ellipse constructor options. |
| Interface | EmitterParticleOptions | Defines parameters of particles used by emitters. |
| Interface | ErrorInformation | Defines error information for card loading. |
| Interface | FocusMovement | Defines the next focus item. |
| Interface | FolderStackOptions | FolderStack constructor options. |
| Interface | FormSize | Defines the size of Form. |
| Interface | FullscreenInfo | Fullscreen information of the video. |
| Interface | GaugeOptions | Defines Gauge constructor options. |
| Interface | ImageSourceSize | Defines source size of image. |
| Interface | LineOptions | Defines Line constructor options. |
| Interface | LinearGradientOptions | Defines the options of linear gradient. |
| Interface | ListDividerOptions | Defines List divider opotions. |
| Interface | ListOptions | Defines List constructor options. |
| Interface | MarqueeOptions | Defines Marquee constructor options. Anonymous Object Rectification. |
| Interface | OnFoldStatusChangeInfo | Information when onFolderStateChange. |
| Interface | OnScrollFrameBeginHandlerResult | The data returned by the event handler when onScrollFrameBegin. |
| Interface | ParticleColorOptions | Defines the particle color options. |
| Interface | ParticleColorUpdaterOptions | Defines the particle color updater options. |
| Interface | ParticleUpdaterOptions | Defines the particle updater options. |
| Interface | PathOptions | Define options used to construct a path. |
| Interface | PlaybackInfo | Playback information of the video. |
| Interface | PluginComponentOptions | Define options used to construct a plugin component. AnonyMous Object Rectificat |
| Interface | PluginErrorData | Data provided when an error occurs. AnonyMous Object Rectification |
| Interface | PolygonOptions | Define options used to construct a polygon. |
| Interface | PolylineOptions | Define options used to construct a polyline. |
| Interface | PopupCommonOptions | Popup common options |
| Interface | PopupMaskType | Popup mask type |
| Interface | PopupStateChangeParam | Popup state change param |
| Interface | PosterOptions | Defines the video poster options. |
| Interface | PreparedInfo | Prepared information of the video. |
| Interface | PreviewMenuOptions | Defines the preview menu options. |
| Interface | RadialGradientOptions | Defines the options of radial gradient. |
| Interface | RatingOptions | Define options used to construct a rating. |
| Interface | RectOptions | Define options used to construct a rectangle. |
| Interface | ReuseOptions | Defining the reusable configuration parameters. |
| Interface | RoundedRectOptions | Define options used to construct a rectangle with rounded corners. |
| Interface | RowOptions | Define options used to construct a row. |
| Interface | RowOptionsV2 | Define options used to construct a row. |
| Interface | SearchOptions | Options used to construct the search. Anonymous Object Rectification. |
| Interface | SheetInfo | The information of sheet. |
| Interface | StackOptions | Options used to construct the stack. |
| Interface | StarStyleOptions | Define star style options. |
| Interface | SweepGradientOptions | Defines the options of radial gradient. |
| Interface | SwiperAutoFill | Set Swiper column count adaptation. |
| Interface | TabBarOptions | Icon and text for TabBar. |
| Interface | TargetInfo | Defines the target info. |
| Interface | TextClockOptions | Options to construct TextClock component. |
| Interface | TextMarqueeOptions | Defines the marquee options. |
| Interface | TextMenuOptions | Defines text menu options. |
| Interface | TextOverflowOptions | Text overflow options. Anonymous Object Rectification. |
| Interface | ToggleOptions | Defines the toggle options. |
| Interface | VelocityOptions | Defines velocity options. |
| Interface | ViewportRect | Viewport bounding box. |

#### 未知模块 (+28：Class 0 / Interface 17 / Enum 11)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | AbilityFlag | Used to query the enumeration value of abilityInfo. Multiple values can be passe |
| Enum | ApplicationFlag | Used to query the enumeration value of applicationInfo. Multiple values can be p |
| Enum | ExtensionAbilityFlag | Used to query the enumeration value of ExtensionAbilityInfo. Multiple values can |
| Enum | ExtensionAbilityType | This enumeration value is used to identify various types of extension ability |
| Enum | ParallelStrategy | ParallelStrategy |
| Enum | ProcessPriority | Describes the level of BackgroundProcessManager priority. |
| Enum | QualityLevel | Levels of processing quality for detail enhancement. |
| Enum | SecurityLevel | Describes the security level. |
| Enum | SteadyStandingStatus | Enum for steady standing status. |
| Enum | StorageType | the storage type |
| Enum | WrapType | An enum type indicates the type of Asset encapsulation. |
| Interface | ApnInfo | Defines the APN info. |
| Interface | AudioCapturerFilter | Describe audio capturer filter. |
| Interface | AuthToken | Authentication token. |
| Interface | CacheDownloadOptions | Options of the cache download task. |
| Interface | ContinueResultInfo | Continue result info. |
| Interface | Edge | Defines Edge Type. |
| Interface | GlobalError | Defines GlobalError. |
| Interface | ImageProcessor | Provides the ImageProcessor type, including the processing function. |
| Interface | OppServerProfile | Manager OPP server profile. |
| Interface | Path | Defines Path Type. |
| Interface | PathSegment | Defines PathSegment Type. |
| Interface | PeerInfo | Collaborative application information. |
| Interface | Result | The GQL statement execution result. |
| Interface | StoreConfig | Manages graph database configurations. |
| Interface | Transaction | Provides transactional methods for managing the graph database. |
| Interface | Vertex | Defines Vertex Type. |
| Interface | VirtualScreenConfig | The parameter for creating virtual screen. |

#### @kit.ArkGraphics3D (+9：Class 5 / Interface 2 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | CubeGeometry | Define a rectangular cuboid. |
| Class | CustomGeometry | An array of vertices and their data defining a custom geometric shape. |
| Class | GeometryDefinition | Define a geometric shape for mesh creation. |
| Class | PlaneGeometry | Define a plane. |
| Class | SphereGeometry | Define a sphere. |
| Enum | GeometryType | Types of geometric shapes. |
| Enum | PrimitiveTopology | How vertices in a sequence form triangles. |
| Interface | BloomSettings | Defines bloom parameters. |
| Interface | MeshResource | Mesh resource. |

#### @kit.ArkWeb (+3：Class 2 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | ProxyController | This class is used for set proxy for ArkWeb. |
| Class | ProxyRule | The ProxyRule used by insertProxyRule. |
| Interface | EmbedOptions | Defines the Embed Options. |

#### @kit.FormKit (+2：Class 2 / Interface 0 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | FormEditExtensionAbility | The class of form edit extension ability. |
| Class | FormEditExtensionContext | The context of form edit extension. It allows access to formEditExtension-specif |

#### @kit.InputKit (+2：Class 0 / Interface 1 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | TouchGestureAction | Enumerates touchscreen gesture action types. |
| Interface | TouchGestureEvent | Defines a touchscreen gesture event. |

#### @kit.NotificationKit (+2：Class 0 / Interface 1 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | LiveViewTypes | Enum for live view notification task type. |
| Interface | NotificationIconButton | Describes a system live view button with icon. |

#### @kit.ArkTS (+1：Class 0 / Interface 0 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | ThreadWorkerPriority | The ThreadWorkerPriority defines the worker priority. |

#### @kit.ConnectivityKit (+1：Class 0 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | BarcodeTag | Provides methods for accessing Barcode tag. |

#### @kit.TestKit (+1：Class 0 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | TouchPadSwipeOptions | Additional options touchpad multi-finger swipe gestures. |

### 2.3 删除类/接口/枚举（按模块）

#### 未知模块 (-5)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | DisplayState | Enumerates the display states. |
| Enum | FoldDisplayMode | Enumerates the fold display mode. |
| Enum | FoldStatus | Enumerates the fold status. |
| Enum | Orientation | Enumerates the display orientation. |
| Interface | Options | Manages preferences file configurations. |

#### @kit.ArkUI (-1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | ParticleOptions | Defines the ParticleOptions Interface. |

### 2.4 方法/属性变化

| 类型 | 模块 | 变化量 |
|------|------|--------|
| +Property | 未知模块 | +369 |
| +Method | 未知模块 | +241 |
| +Property | @kit.ArkUI | +30 |
| +Method | @kit.ArkWeb | +2 |
| -Method | 未知模块 | -12 |
| -Property | 未知模块 | -10 |

## 二、5.1 → 6.0（架构重构——API体系换代）

### 2.1 总览

| 维度 | 新增 | 删除 | 净变化 |
|------|------|------|--------|
| 类/接口/枚举 | +228 | -222 | +6 |
| 方法/属性 | +1096 | -804 | +292 |

### 2.2 新增类/接口/枚举（按模块）

#### @kit.ArkUI (+117：Class 17 / Interface 68 / Enum 32)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Binding | Represents a read-only data binding. Use with @Builder argument list for primiti |
| Class | ColorShaderStyle | Defines a shader with single color. |
| Class | ContentTransition | Defines the text content transition class. |
| Class | Gesture | Defines Gesture interface. |
| Class | LazyGridLayoutAttribute | Defines the lazy grid layout attribute. |
| Class | LazyVGridLayoutAttribute | Defines the lazy vertical grid layout attribute. |
| Class | LinearGradientStyle | Defines linear gradient class. |
| Class | MutableBinding | Represents a mutable data binding allowing both read and write operations. Use w |
| Class | NumericTextTransition | Defines the numeric text content transition class. |
| Class | PageTransitionEnter | Provides an interface to set transition style when a page enters. |
| Class | PageTransitionExit | Provide an interface to set transition style when a page exits. |
| Class | RadialGradientStyle | Defines radial gradient class. |
| Class | ShaderStyle | Defines shader style class. |
| Class | StepperModifier | Defines Stepper Modifier |
| Class | ToolBarItemAttribute | Defines the ToolBarItem component attribute functions. |
| Class | TouchRecognizer | Defines the touch recognizer. |
| Class | TypedFrameNode | Used to define the FrameNode type. |
| Enum | AccessibilityAction | Enum for accessibility action type |
| Enum | AccessibilityActionInterceptResult | Enum for the result of accessibility action intercept function |
| Enum | AnimationPropertyType | Define the property type enumeration used in animation. |
| Enum | AutoCapitalizationMode | Declare the type of automatic case mode switching. |
| Enum | AvailableLayoutArea | Defines the available layout area. |
| Enum | AvoidanceMode | Enumeration of avoidance modes for the Select dropdown menu |
| Enum | ColorSpace | Define ColorSpace enumeration. |
| Enum | DividerMode | Menu divider mode. |
| Enum | DraggingSizeChangeEffect | Define drag start animation effect from drag preview to the handle drag image |
| Enum | EffectLayer | Effect layer enum. |
| Enum | EventQueryType | Event query type. |
| Enum | FlipDirection | Defines the flip direction of numeric text transition. |
| Enum | FocusDrawLevel | Type of focus draw level. |
| Enum | FocusWrapMode | Focus wrap mode of a list or grid when moving focus using the arrow keys. |
| Enum | GestureActionPhase | This is an enumeration type representing the gesture callback phases to be trigg |
| Enum | GestureListenerType | This is an enumeration type indicating what kind of gesture you want to monitor  |
| Enum | KeyboardFluidLightMode | Keyboard fluid light mode. |
| Enum | KeyboardGradientMode | Keyboard Gradient mode. |
| Enum | LocalizedAlignment | Alignment enumeration description. |
| Enum | MaxLinesMode | Defines maxlines mode. |
| Enum | ModalMode | Define the modal mode of menu. |
| Enum | NodeRenderState | An enumeration type that identifies the current node's rendering state. The UI c |
| Enum | PreviewScaleMode | Defines the scaling mode for custom preview of contextMenu. |
| Enum | ReplaceEffectType | The replace effect type of symbol. |
| Enum | SuperscriptStyle | Defines the superscript style. |
| Enum | TabsCacheMode | Declare the cache mode of the child components. |
| Enum | TextChangeReason | Defines the reason for text changes. |
| Enum | TextVerticalAlign | Vertical Alignment of text. |
| Enum | TipsAnchorType | Follow position type. |
| Enum | ToolBarItemPlacement | Declare the placement of the toolbar item. |
| Enum | UIState | Enum for the UI state of one component, which is used for handling of state styl |
| Enum | UndoStyle | Defines undo style. |
| Interface | AlignRuleParam | Defines the align rule options of relative container. |
| Interface | AsymmetricTransitionOption | Defines the option of asymmetric transition. |
| Interface | BackgroundOptions | Defines background options. |
| Interface | Bindable | Defines a bindable property |
| Interface | BorderRadiuses | Defines the border radius property. Anonymous Object Rectification |
| Interface | ButtonLabelStyle | ButtonLabelStyle object. |
| Interface | CalendarRequestedMonths | Defines the struct of CalendarRequestedMonths. |
| Interface | DateRange | Defines a range of dates. |
| Interface | DecorationOptions | Defines DecorationOptions for Decoration. |
| Interface | DynamicNode | Define DynamicNode. |
| Interface | EdgeColors | Defines the border color property. Anonymous Object Rectification |
| Interface | EdgeOutlineStyles | Defines the outline style property. |
| Interface | EdgeOutlineWidths | Defines the outline width property. |
| Interface | EdgeStyles | Defines the border style property. Anonymous Object Rectification |
| Interface | EdgeWidths | Defines the border width property. Anonymous Object Rectification |
| Interface | EffectComponentOptions | Defines the Effect Component constructor options. |
| Interface | EventLocationInfo | The location info used in gesture event. |
| Interface | GestureObserverConfigs | The observer options for global gesture listener. |
| Interface | GestureTriggerInfo | The information when one gesture specific callback is triggered. |
| Interface | HomePathInfo | Indicates the information of home destination. |
| Interface | IMEClient | Defines the input method client. |
| Interface | ImageCompleteEvent | ImageCompleteEvent |
| Interface | InteractionEventBindingInfo | The interaction event binding status information on the component. |
| Interface | ItemDragEventHandler | Define item drag event handler. |
| Interface | KeyboardAppearanceConfig | Defines the keyboard appearance config. |
| Interface | LengthConstrain | Defines the length constrain property. Anonymous Object Rectification |
| Interface | LineSpacingOptions | Defines the line spacing options. |
| Interface | MaxLinesOptions | Defines the options of max lines. |
| Interface | MenuMaskType | Menu mask type |
| Interface | MenuOutlineOptions | The declare of menuOutlineOptions. |
| Interface | MonitorOptions | Define Monitor options. |
| Interface | MoreButtonOptions | Indicates the options of Navigation's Menu. |
| Interface | NativeXComponentParameters | Defines the native xcomponent parameters. |
| Interface | NavigationMenuOptions | Indicates the options of Navigation's Menu. |
| Interface | NumericTextTransitionOptions | The options of numeric text transition. |
| Interface | Offset | Defines the offset property. |
| Interface | OutlineRadiuses | Defines the outline radius property. |
| Interface | Padding | Defines the padding property. Anonymous Object Rectification |
| Interface | ParticleAnnulusRegion | Defines particle annuslus region params. |
| Interface | ParticleOptions | Defines the ParticleOptions Interface. |
| Interface | Particles | Defines the Particles interface. |
| Interface | PickerBackgroundStyle | Provide an interface to set the background style of selected items. |
| Interface | PopupBorderLinearGradient | Popup border LinearGradient |
| Interface | PopupButton | Defines the popup button. |
| Interface | RichEditorUrlStyle | RichEditor url style. |
| Interface | RotateAngleOptions | The rotation parameters containing multi-axis angle information. |
| Interface | ScrollBarMargin | Define scrollbar margin options. |
| Interface | SliderCustomContentOptions | Defines the options for customizing the accessibility of content within a slider |
| Interface | SliderPrefixOptions | Options used for customizing the prefix part of the slider. It extends the Slide |
| Interface | SliderShowStepOptions | Defines the accessibility information of slider step point. |
| Interface | SliderStepItemAccessibility | Defines the accessibility information of slider step point. |
| Interface | SliderSuffixOptions | Options used for customizing the suffix part of the slider. It extends the Slide |
| Interface | SubTabBarIndicatorStyle | Provide an interface for the style of an SubTabBar indicator including color, he |
| Interface | SymbolGlyphModifier | Defines SymbolGlyph Modifier |
| Interface | SystemAdaptiveOptions | Defines the SystemAdaptiveOptions interface |
| Interface | TabBarLabelStyle | TabBarLabelStyle object. |
| Interface | TextLayoutOptions | Defines text layout options. Use this to set constraints for measure text. |
| Interface | TextModifier | Defines Text Modifier |
| Interface | TextPickerDialogOptionsExt | Defines the TextPickerDialogOptionsExt for Text Picker Dialog. |
| Interface | TipsOptions | Defines the Tips options. |
| Interface | ToolBarItemInterface | Defines the ToolBarItem Component. |
| Interface | ToolBarItemOptions | ToolBarItem constructor options. |
| Interface | UIGridEvent | Defines a UIGridEvent which is used to set event to target component. |
| Interface | UIListEvent | Defines a UIListEvent which is used to set different common event to target comp |
| Interface | UIScrollEvent | Defines a UIScrollableCommonEvent which is used to set different common event to |
| Interface | UIScrollableCommonEvent | Defines a UIScrollableCommonEvent which is used to set event to target component |
| Interface | UIWaterFlowEvent | Defines a UIWaterFlowEvent which is used to set event to target component. |
| Interface | XComponentParameter | Defines the XComponent parameter interface. |

#### 未知模块 (+42：Class 3 / Interface 25 / Enum 14)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | FastBuffer | The FastBuffer object is a method of handling buffers dedicated to binary data. |
| Class | ListFrameNode | Define the List type of FrameNode. |
| Class | XmlDynamicSerializer | The XmlDynamicSerializer interface is used to dynamically generate an xml file. |
| Enum | AudioLoopbackMode | Enumerates audio loopback mode. |
| Enum | AudioLoopbackStatus | Enumerates audio loopback status. |
| Enum | CustomResult | custom 802.1x result. |
| Enum | DeviceTypes | Enumerates thedevice types. |
| Enum | DialogType | The enum of bluetooth dialog type. |
| Enum | EventType | Enum for control event type |
| Enum | HiTraceOutputLevel | Enumerates the HiTrace output levels. The output level threshold system paramete |
| Enum | HoldingHandStatus | Enum for holding hand status |
| Enum | JsRawHeapTrimLevel | Trimming level of raw heap snapshot. |
| Enum | KioskFeature | Enum for Kiosk Feature. |
| Enum | Scenario | Enum for page content scenario |
| Enum | SimType | Indicates the SIM card type. |
| Enum | SupportedImageFormat | Enumerates the types of av file format. |
| Enum | SystemSoundError | Error enum for system sound. |
| Interface | ConnectResult | Describes the result of connect operation. |
| Interface | ContentOptions | Interface for content options |
| Interface | ControlEvent | Interface for control event |
| Interface | DataInfo | Data information structure. |
| Interface | DeviceRotationRadian | Interface for device rotation radian |
| Interface | DomainAccountPolicy | The policy of domain account |
| Interface | DownloadInfo | Download information of historical cache downloads. |
| Interface | EapData | Describes the EAP information. |
| Interface | EffectInfo | The information includes Indicates whether the effect is supported. |
| Interface | FloatingBallConfiguration | FloatingBallConfiguration |
| Interface | FloatingBallController | FloatingBallController |
| Interface | GwpAsanOptions | GwpAsan Options. |
| Interface | MechInfo | Mechanical device information. |
| Interface | NetworkInfo | Network information of historical cache downloads. |
| Interface | NotifyDialogResultParams | Describes the result of bluetooth dialog. |
| Interface | PageContent | Interface for pageContent |
| Interface | Paragraph | Interface for paragraph |
| Interface | PerformanceInfo | Performance information of historical cache downloads. |
| Interface | ResourceInfo | Resource information of historical cache downloads. |
| Interface | SelectionInfo | Defines the information of a word selection event. |
| Interface | SerialPort | Represents a serial port device. |
| Interface | SyncResult | Interface of synchronization result. |
| Interface | TransientTaskInfo | The callback info of transient task. |
| Interface | TypedArray | TypedArray inherits the features and methods of Int8Array |
| Interface | UserClassification | Represents the classification result of the user based on age group, including t |

#### @kit.AbilityKit (+21：Class 5 / Interface 14 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | AppServiceExtensionAbility | class of app service extension ability. |
| Class | AppServiceExtensionContext | The context of app service extension. It allows access to AppServiceExtension-sp |
| Class | CompletionHandler | CompletionHandler is a handler to handle the completion events of start ability. |
| Class | CompletionHandlerForAtomicService | CompletionHandlerForAtomicService is a handler to handle the completion events o |
| Class | InsightIntentEntryExecutor | The class of insight intent entry executor. |
| Enum | FailureCode | Specific failure codes indicating failure to open atomicservice. |
| Enum | LinkParamCategory | Enum definition of the paramCategory {@link #LinkIntentParamMapping#paramCategor |
| Interface | BundleOptions | The bundle options of bundle manager |
| Interface | DynamicIconInfo | Obtains dynamic icon information about a bundle |
| Interface | EntryIntentDecoratorInfo | Declare interface of EntryIntentDecoratorInfo. |
| Interface | FormIntentDecoratorInfo | Declare interface of FormIntentDecoratorInfo. |
| Interface | FunctionIntentDecoratorInfo | Declare interface of FunctionIntentDecoratorInfo. |
| Interface | IntentDecoratorInfo | Declare interface of IntentDecoratorInfo. |
| Interface | IntentEntityDecoratorInfo | Declare interface of IntentEntityDecoratorInfo. |
| Interface | KioskStatus | The Kiosk status data. |
| Interface | LinkIntentDecoratorInfo | Declare interface of LinkIntentDecoratorInfo. |
| Interface | LinkIntentParamMapping | Declare interface of LinkIntentParamMapping. |
| Interface | LocalWantAgentInfo | Provides the information required to create a local WantAgent. |
| Interface | PageIntentDecoratorInfo | Declare interface of PageIntentDecoratorInfo. |
| Interface | PluginBundleInfo | Provides information about a plugin. |
| Interface | PluginModuleInfo | Indicates the plugin module info. |

#### @kit.ArkGraphics3D (+14：Class 0 / Interface 11 / Enum 3)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | CullMode | The enum of PBR material cull mode. |
| Enum | SamplerAddressMode | Addressing mode for Sampler |
| Enum | SamplerFilter | Sampler filter Mode |
| Interface | Blend | Blend interface. |
| Interface | MaterialProperty | Material property interface. |
| Interface | MetallicRoughnessMaterial | Physically-based metallic roughness material resource. |
| Interface | Morpher | Defines Morpher interface for specifying morph targets for Node's geometry. |
| Interface | RaycastParameters | How a raycast should be performed. |
| Interface | RaycastResult | The result of a ray cast hit. |
| Interface | RenderContext | Render context defines the context for all rendering resources. Resources within |
| Interface | RenderResourceFactory | The render resource factory. RenderResourceFactory is used to create resources t |
| Interface | RenderSort | Render sort Layer. Within a render slot a layer can define a sort layer order. T |
| Interface | Sampler | Sampler interface |
| Interface | SceneComponent | Define underlying scene component |

#### @kit.ArkWeb (+10：Class 0 / Interface 6 / Enum 4)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | AudioSessionType | Arkweb audio session Type |
| Enum | GestureFocusMode | Enum type supplied to {@link gestureFocusMode} for setting the web gesture focus |
| Enum | PdfLoadResult | PDF page load result |
| Enum | WebBypassVsyncCondition | Enum type supplied to {@link bypassVsyncCondition} for setting the bypass vsync  |
| Interface | NativeEmbedMouseInfo | Defines the user mouse info on embed layer. |
| Interface | OnLoadFinishedEvent | Defines the triggered function at the end of web page loading. |
| Interface | OnLoadStartedEvent | Defines the triggered function at the begin of web page loading. |
| Interface | OnPdfLoadEvent | Defines the function Triggered when the PDF load. |
| Interface | OnPdfScrollEvent | Defines the function Triggered when the PDF page scrolling. |
| Interface | PreviewMenuOptions | Defines the options of preview menu |

#### @kit.AccessibilityKit (+6：Class 1 / Interface 3 / Enum 2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Parameter | Indicates the parameter of the AccessibiltyAction. |
| Enum | AccessibilityAction | Accessibility action that the ability can execute. |
| Enum | AccessibilityEventType | AccessibilityEvent type |
| Interface | AccessibilityEventInfo | Indicates the accessibility event. It provides the event type and the target ele |
| Interface | AccessibilityGrid | Indicates grid info. |
| Interface | AccessibilitySpan | Indicates span info. |

#### @kit.TestKit (+5：Class 1 / Interface 3 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | PerfTest | The unified facade of PerformanceTest framework, can be used to executing the pe |
| Enum | PerfMetric | Enumerates the metric type of performance test. |
| Interface | InputTextMode | Text input method options. |
| Interface | PerfMeasureResult | Test results of specified performance metric. |
| Interface | PerfTestStrategy | Test task execution strategy, which is used to initialize the PerfTest object in |

#### @kit.BasicServicesKit (+4：Class 2 / Interface 1 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | SelectionExtensionAbility | Defines the class of the ExtensionAbility for word selection. |
| Class | SelectionExtensionContext | Defines the ExtensionContext for the word selection service. |
| Enum | PanelType | Enumerates the types of the word selection panel. |
| Interface | PanelInfo | Defines information about the word selection panel. |

#### @kit.DistributedServiceKit (+3：Class 2 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | DistributedExtensionAbility | Class to be override for distributed extension ability. |
| Class | DistributedExtensionContext | Class inherited for the distributed extension function. |
| Interface | DataInfo | Data information structure. |

#### @kit.FormKit (+3：Class 2 / Interface 1 / Enum 0)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | LiveFormExtensionAbility | The class of live form extension ability. |
| Class | LiveFormExtensionContext | The context of live form extension. It allows access to liveFormExtension-specif |
| Interface | LiveFormInfo | Provides information about a live form. |

#### @kit.MediaKit (+2：Class 0 / Interface 1 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | ErrorType | Enumerates the error type. |
| Interface | ErrorInfo | Interface for error info. |

#### @kit.InputKit (+1：Class 0 / Interface 0 / Enum 1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Enum | FixedMode | Fixed mode of screenX and screenY. |

### 2.3 删除类/接口/枚举（按模块）

#### @kit.ArkUI (-123)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Font | class Font |
| Class | IndicatorComponentController | Provides methods for switching components. |
| Class | LocationButtonAttribute | Defines the attributes of the location button. |
| Class | NodeController | Defined the controller of node container.Provides lifecycle callbacks for the as |
| Class | PanGestureOptions | Defines the PanGesture options. |
| Class | RenderNode | Defines RenderNode. Contains node tree operations and render property operations |
| Class | SearchController | Provides the method of switching the cursor position. |
| Class | SpringProp | Customize spring properties. |
| Class | SwiperController | Provides methods for switching components. |
| Class | SymbolGlyphModifier | Defines SymbolGlyph Modifier |
| Class | TextAreaController | Provides the method of switching the cursor position. |
| Class | TextClockController | Provides a way to control the textclock status. |
| Class | TextModifier | Defines Text Modifier |
| Class | TextTimerController | Provides a way to control the process. |
| Enum | BadgePosition | Defines the badge position property. |
| Enum | ButtonType | Provides a button component. |
| Enum | CalendarAlign | The type of alignment between entry and calendar. |
| Enum | DataPanelType | DataPanelType enum |
| Enum | DialogAlignment | The alignment of dialog, |
| Enum | DpiFollowStrategy | Enumeration of different types of DpiFollowStrategy. |
| Enum | FormDimension | Defines the FormDimension enum. |
| Enum | GesturePriority | Creating an Object |
| Enum | GridItemStyle | Defines the grid item style. |
| Enum | IndexerAlign | indexer align property. |
| Enum | InputType | Declare the type of input box |
| Enum | ItemState | ItemState |
| Enum | LevelMode | Define the display mode of all kind of dialog |
| Enum | ListItemGroupStyle | Defines the list item group style. |
| Enum | LoadingProgressStyle | Load style of progress bar. |
| Enum | LocationButtonOnClickResult | Enumerates the click event results of the location button. |
| Enum | LocationDescription | Enumerates the text that can be displayed on the location button. |
| Enum | LocationIconStyle | Enumerates the icon styles. |
| Enum | NodeRenderType | Render type of the node using for indicating that if the node will be shown on t |
| Enum | PanDirection | Creating an Object |
| Enum | PatternLockChallengeResult | The challenge result based on input pattern for control pattern lock component. |
| Enum | RadioIndicatorType | Defines the IndicatorType of Radio component |
| Enum | RefreshStatus | The refresh status of the drop-down refresh. |
| Enum | RichEditorDeleteDirection | Defines delete text direction. |
| Enum | RouteType | Declare the jump method. |
| Enum | ScrollBarDirection | Content scroll direction. |
| Enum | ScrollDirection | Content scroll direction. |
| Enum | ScrollState | Declare scroll status |
| Enum | SeekMode | Seek mode. |
| Enum | SelectStatus | CheckboxGroup SelectStatus |
| Enum | SelectedMode | Enum for the mode of the tab bar when selected. |
| Enum | SideBarContainerType | Sets the sidebar style of showing |
| Enum | SliderStyle | Declare sliderstyle |
| Enum | Sticky | Declare item ceiling attribute. |
| Enum | TextDataDetectorType | Defines the text data detector type. |
| Enum | ToggleType | Declare the type of status button |
| Interface | ASTCResource | Defines the resource which can use ASTC. |
| Interface | AnimatorOptions | Defines the animator options. |
| Interface | BlankInterface | Create Blank. |
| Interface | CalendarDay | Provides a monthly view component to display information such as date, shift bre |
| Interface | CheckboxOptions | Defines the options of Checkbox. |
| Interface | CircleOptions | Defines circle options for Circle component. |
| Interface | ColumnSplitInterface | Defines the ColumnSplit component. |
| Interface | ContainerSpanInterface | Span container interface. |
| Interface | CounterInterface | Counter component, which provides corresponding increment or decrement counting  |
| Interface | CustomDialogControllerOptions | Defines the options of CustomDialogController. |
| Interface | DatePickerResult | Defines the struct of DatePickerResult. |
| Interface | DividerInterface | Provides a divider component to separate different content blocks/content elemen |
| Interface | EffectComponentInterface | Provides an Effect Component, which is invisible, but setting properties on this |
| Interface | EllipseOptions | Ellipse constructor options. |
| Interface | EmbeddedComponentInterface | Provide an interface for the EmbeddedComponent, which is used <br/>to render UI  |
| Interface | FlexOptions | Defines the options of Flex. |
| Interface | FlowItemInterface | Mesh container for static fixed-size layout scenarios. |
| Interface | FocusBoxStyle | Focus box style. |
| Interface | FormLinkOptions | Defines the FormLink options. |
| Interface | GaugeOptions | Defines Gauge constructor options. |
| Interface | GestureGroupGestureHandlerOptions | Defines the GestureGroupGestureHandler options. |
| Interface | GestureGroupInterface | Defines the GestureGroup interface. |
| Interface | GridColColumnOption | Defines the option in number unit of grid-container child component. |
| Interface | GridLayoutOptions | The options to help grid layout |
| Interface | GridRowSizeOption | Defines the option in length unit of grid-row component. |
| Interface | HyperlinkInterface | Defines the hyperlink interface. |
| Interface | ImageAnimatorInterface | Defines the ImageAnimator Interface. |
| Interface | ImageSpanInterface | Provide image decoration in the text component. |
| Interface | LayoutConstraint | Layout constraint, include the max size, the min size and the reference size for |
| Interface | LocationButtonInterface | Defines the interface for setting a location button. |
| Interface | LocationButtonOptions | Declares the interface for setting the location button options. |
| Interface | LongPressGestureHandlerOptions | Defines the LongPressGestureHandler options. |
| Interface | LongPressGestureInterface | Defines LongPressGesture interface extends GestureInterface<LongPressGestureInte |
| Interface | MarqueeOptions | Defines Marquee constructor options. Anonymous Object Rectification. |
| Interface | MeasureOptions | Defines the options of MeasureText. |
| Interface | MenuInterface | Defines the Menu Component. |
| Interface | MenuItemGroupOptions | Defines the option of MenuItemGroup. |
| Interface | MenuItemOptions | Defines the option of MenuItem. |
| Interface | NodeContainerInterface | Defines the Interface of NodeContainer. To display the node build by an associat |
| Interface | PanGestureHandlerOptions | Defines the PanGestureHandler options. |
| Interface | PathOptions | Define options used to construct a path. |
| Interface | PinchGestureHandlerOptions | Defines the PinchGestureHandler options. |
| Interface | PinchGestureInterface | Defines PinchGesture interface extends GestureInterface<PinchGestureInterface>. |
| Interface | PolygonOptions | Define options used to construct a polygon. |
| Interface | PolylineOptions | Define options used to construct a polyline. |
| Interface | QRCodeInterface | Provides an interface for generating QR codes. |
| Interface | RRect | Round rect. |
| Interface | RatingOptions | Define options used to construct a rating. |
| Interface | RelativeContainerInterface | Provides ports for relative containers. |
| Interface | RichTextInterface | Provides an interface for RichText component. |
| Interface | RootSceneSession | Defines the session of RootScene. |
| Interface | RotationGestureHandlerOptions | Defines the RotationGestureHandler options. |
| Interface | RotationGestureInterface | Defines RotationGesture interface extends GestureInterface<RotationGestureInterf |
| Interface | RowOptions | Define options used to construct a row. |
| Interface | RowSplitInterface | Provides interfaces for layout in the vertical direction. |
| Interface | ScreenInterface | Defines the interface of Screen. |
| Interface | SelectOption | The declare of selectOption. |
| Interface | ShapeSize | Interface for shape size properties. |
| Interface | SheetInfo | The information of sheet. |
| Interface | StackOptions | Options used to construct the stack. |
| Interface | SurfaceRect | Surface Rectangle information. |
| Interface | SwipeGestureHandlerOptions | Defines the SwipeGestureHandler options. |
| Interface | SwipeGestureInterface | Defines SwipeGesture interface extends GestureInterface<SwipeGestureInterface>. |
| Interface | SymbolGlyphInterface | Provides an interface for SymbolGlyph. |
| Interface | SymbolSpanInterface | Provides an interface for SymbolSpan. |
| Interface | TapGestureHandlerOptions | Defines the TapGestureHandler options. |
| Interface | TextBackgroundStyle | Define the background style of span. |
| Interface | TextOverflowOptions | Text overflow options. Anonymous Object Rectification. |
| Interface | TextPickerRangeContent | Define the contents of each selector item. |
| Interface | Theme | Defines the struct of Theme. |
| Interface | TimePickerResult | Defines the struct of TimePickerResult. |
| Interface | ViewportRect | Viewport bounding box. |
| Interface | WindowSceneInterface | Defines the interface of WindowScene. |

#### 未知模块 (-76)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Duplex | Duplex streams are streams that implement both the Readable streams and Writable |
| Class | HashStream | Hash Stream. |
| Class | Readable | The stream from which data can be read. |
| Class | System | Provides system functions. |
| Class | Transform | Transform stream is a Duplex stream where the output is computed in some way fro |
| Class | XmlSerializer | The XmlSerializer interface is used to generate an xml file. |
| Class | unnamed | Obtains the classification of this notification. |
| Enum | AbilityFlag | Used to query the enumeration value of abilityInfo. Multiple values can be passe |
| Enum | AbilityState | Enum for the ability state. |
| Enum | ActiveDeviceType | Enumerates the active device types. |
| Enum | ApplicationFlag | Used to query the enumeration value of applicationInfo. Multiple values can be p |
| Enum | ApplicationState | Enum for the application state |
| Enum | AssetStatus | Describes the status of asset |
| Enum | AudioChannel | Enumerates the audio channel. |
| Enum | AudioEncodingType | Enumerates the audio encoding type. |
| Enum | AudioPrivacyType | Enumerates audio stream privacy type for playback capture. |
| Enum | AudioRingMode | Enumerates ringer modes. |
| Enum | AudioSampleFormat | Enumerates the audio sample formats. |
| Enum | AudioSamplingRate | Enumerates the audio sampling rate. |
| Enum | AuthenticationResult | Enum for authentication result. |
| Enum | BundleFlag | Used to query the enumeration value of bundleInfo. Multiple values can be passed |
| Enum | BundlePackFlag | Used to query the enumeration value of bundlePackInfo. |
| Enum | CommunicationDeviceType | Enumerates the available device types for communication. |
| Enum | ContentType | Enumerates the audio content type. |
| Enum | Direction | Enumerates screen directions. |
| Enum | DragStatus | Defines the Drag Status. |
| Enum | ErrorCode | The error code of rpc. |
| Enum | ExtensionAbilityFlag | Used to query the enumeration value of ExtensionAbilityInfo. Multiple values can |
| Enum | ExtensionAbilityType | This enumeration value is used to identify various types of extension ability |
| Enum | InterruptRequestType | Enumerates the audio interrupt request type. |
| Enum | LogLevel | Log level define |
| Enum | NavDestinationState | NavDestination state. |
| Enum | OperationMode | Enumerates the uri operate mode types. |
| Enum | Pattern | Enumerates the patterns allowed in the system pasteboard. |
| Enum | PointerStyle | Pointer style. |
| Enum | PolicyType | Enumerates type. |
| Enum | ResourceFlag | Used to query the enumeration value of resource info. Multiple values can be pas |
| Enum | RingtoneType | Enum for ringtone type. |
| Enum | SecurityLevel | Describes the security level. |
| Enum | ShareOption | Types of scope that PasteData can be pasted. |
| Enum | StreamUsage | Enumerates the stream usage. |
| Enum | TextAlign | Refers to how to align the horizontal position of text when displaying text. |
| Enum | UpgradeFlag | Used to set the enumeration value of upgrading for free installation. |
| Enum | VolumeFlag | Enumerates volume related operations. Flags should be powers of 2! |
| Enum | WantAgentFlags | Enumerates flags for using a WantAgent. |
| Interface | AudioCapturerFilter | Describe audio capturer filter. |
| Interface | AudioRendererFilter | Describes audio renderer filter. |
| Interface | AudioRendererInfo | Describes audio renderer information. |
| Interface | AudioRendererOptions | Describes audio renderer configuration options. |
| Interface | AudioStreamInfo | Describes audio stream information. |
| Interface | DragAction | One drag action object for drag process |
| Interface | DragAndDropInfo | Drag and drop information |
| Interface | Edge | Defines Edge Type. |
| Interface | Filter | The Filter of FilterChain. |
| Interface | Filter | The Filter for Component. |
| Interface | FontOptions |  |
| Interface | InnerEvent | Describes an intra-process event. |
| Interface | IntervalInfo | Provides the IntervalInfo interface, which includes timestamp and targetTimestam |
| Interface | KeyOptions | Defines event of key that user want to subscribe or unsubscribe. |
| Interface | LaunchParam | Interface of launch param. |
| Interface | MediaQueryResult | Defines the Result of mediaquery. |
| Interface | NetConnection | Represents the network connection handle. |
| Interface | NotificationKey | Describes a NotificationKey, which can be used to identify a notification. |
| Interface | OperatorConfig | Defines the carrier configuration. |
| Interface | PasteDataProperty | Paste data property. |
| Interface | PasteDataRecord | Paste data record. |
| Interface | Path | Defines Path Type. |
| Interface | PathSegment | Defines PathSegment Type. |
| Interface | ReadableOptions | Return readable options. |
| Interface | Result | The GQL statement execution result. |
| Interface | SnapshotRegion | Defines the extra options for snapshot taking. |
| Interface | StoreConfig | Manages graph database configurations. |
| Interface | Transaction | Provides transactional methods for managing the graph database. |
| Interface | Vertex | Defines Vertex Type. |
| Interface | WebHeader | Defines the Web's request/response header. |
| Interface | WindowRect | Window Rectangle |

#### @kit.AbilityKit (-14)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | Ability | The class of an ability. |
| Class | AbilityStartCallback | The callback of UIAbility or UIExtensionAbility. |
| Class | ApplicationContext | The context of an application. It allows access to application-specific resource |
| Class | Context | The base context of an ability or an application. It allows access to applicatio |
| Class | ServiceExtensionContext | The context of service extension. It allows access to serviceExtension-specific  |
| Class | StartOptions | StartOptions is the basic communication component of the system. |
| Class | UIAbilityContext | The context of an ability. It allows access to ability-specific resources. |
| Class | UIExtensionContentSession | class of ui extension content session. |
| Class | UIExtensionContext | The context of UI extension. It allows access to UIExtension-specific resources. |
| Interface | BundleResourceInfo | Obtains resource information about a bundle |
| Interface | LauncherAbilityResourceInfo | Obtains resource information about a launcher ability |
| Interface | OnReleaseCallback | The prototype of the listener function interface registered by the Caller. |
| Interface | ProcessInformation | The class of an process information. |
| Interface | WantAgentInfo | Provides the information required for triggering a WantAgent. |

#### @kit.NotificationKit (-4)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | NotificationActionButton | Describes an action button displayed in a notification. |
| Interface | NotificationRequest | Defines a NotificationRequest instance. |
| Interface | NotificationSlot | Describes a NotificationSlot instance. |
| Interface | NotificationSubscriber | Provides methods that will be called back when the subscriber receives a new not |

#### @kit.ArkWeb (-2)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | ProxyController | This class is used for set proxy for ArkWeb. |
| Class | ProxyRule | The ProxyRule used by insertProxyRule. |

#### @kit.BasicServicesKit (-1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | CommonEventSubscriber | the subscriber of common event |

#### @kit.CoreFileKit (-1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Interface | BundleVersion | Describe bundle version |

#### @kit.FormKit (-1)

| 类型 | 名称 | 描述 |
|------|------|------|
| Class | FormExtensionContext | The context of form extension. It allows access to formExtension-specific resour |

### 2.4 方法/属性变化

| 类型 | 模块 | 变化量 |
|------|------|--------|
| +Property | 未知模块 | +600 |
| +Method | 未知模块 | +459 |
| +Property | @kit.ArkUI | +17 |
| +Method | @kit.ArkUI | +10 |
| +Method | @kit.DistributedServiceKit | +4 |
| +Property | @kit.DistributedServiceKit | +4 |
| +Method | @kit.AbilityKit | +2 |
| -Property | 未知模块 | -429 |
| -Method | 未知模块 | -361 |
| -Property | @kit.ArkUI | -8 |
| -Method | @kit.CoreFileKit | -3 |
| -Method | @kit.ArkWeb | -2 |
| -Method | @kit.ArkUI | -1 |

## 三、API6.0 最终模块版图

| 排名 | 模块 | 类/接口/枚举 | 定位 |
|------|------|-------------|------|
| 1 | @kit.ArkUI | 1396 | UI框架 |
| 2 | 未知模块 | 388 |  |
| 3 | @kit.AbilityKit | 188 | 应用框架 |
| 4 | @kit.ArkWeb | 122 | WebView |
| 5 | @kit.ArkGraphics3D | 60 | 3D图形 |
| 6 | @kit.BasicServicesKit | 38 | 基础服务 |
| 7 | @kit.NotificationKit | 33 | 通知系统 |
| 8 | @kit.CoreFileKit | 32 | 文件系统 |
| 9 | @kit.ArkTS | 29 | 语言运行时 |
| 10 | @kit.InputKit | 26 | 输入 |
| 11 | @kit.TestKit | 26 | 测试框架 |
| 12 | @kit.SensorServiceKit | 24 | 传感器 |
| 13 | @kit.ConnectivityKit | 18 | 连接/NFC |
| 14 | @kit.AccessibilityKit | 14 | 无障碍 |
| 15 | @kit.ArkData | 9 | 数据 |
| 16 | @kit.LocationKit | 8 | 定位 |
| 17 | @kit.FormKit | 6 | 卡片 |
| 18 | @kit.IMEKit | 6 | 输入法 |
| 19 | @kit.MediaLibraryKit | 6 | 媒体库 |
| 20 | @kit.AVSessionKit | 5 |  |

## 四、架构演进关键洞察

### 4.1 三个阶段

1. **API4.1→5.0 框架创立期**：ArkUI、AbilityKit、ArkWeb 三大核心框架从零建立，新增 1,729 个类/接口
2. **API5.0→5.1 增量补全期**：新增圆弧组件体系（圆表适配），手势识别器独立化，3D几何具象化
3. **API5.1→6.0 架构重构期**：AbilityKit 从继承模式转向意图装饰器模式，ArkUI 大规模清理命名规范，分布式能力独立成模块

### 4.2 AbilityKit 的范式转移

API5.1→6.0 中，旧基类 `Ability`、`Context`、`UIAbilityContext` 等被移除，
替换为 `IntentDecoratorInfo`、`PageIntentDecoratorInfo`、`FormIntentDecoratorInfo` 
等意图装饰器模式，标志着从「继承重载」向「声明式组合」的架构转变。

### 4.3 ArkUI 的命名规范化

API5.1→6.0 中删除了 70+ 个旧 `*Interface` 命名（如 `QRCodeInterface`、`PathOptions`），
新增 `Binding`、`Gesture`、`ContentTransition`、`ShaderStyle` 等更现代化的 API 命名。
这是一次系统性的 API 命名重构。

### 4.4 新增独立模块

API5.1→6.0 中 `@kit.DistributedServiceKit` 首次独立出现（`DistributedExtensionAbility`），
标志着分布式能力从应用框架中解耦，成为独立的一级模块。
`@kit.BasicServicesKit` 新增 `SelectionExtensionAbility`，文本选择能力独立化。

---

*报告由 Neo4j 知识图谱自动生成，数据来源：4432 个 JSON API 定义文件*