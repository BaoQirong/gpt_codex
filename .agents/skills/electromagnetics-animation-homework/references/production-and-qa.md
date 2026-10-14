# 制作、LaTeX 与成片检查

## 工程和环境

复制 `assets/project/` 到新项目目录，或修订已有工程。主要源文件：`vector_calculus.py`、`narration.json`、`make_bgm.py`、`verify_video.py`、`render.ps1`、`manim.cfg`。

依赖：Python、Manim Community、PyAV、NumPy、SciPy、Pillow、LaTeX、dvisvgm 和中文字体。模板的 `requirements.txt` 记录本次验证环境的 Python 包版本。LaTeX 的闭合曲面积分 `\oiint` 使用 `esint`；缺包时处理该具体依赖，不把闭合面退回普通二重积分而隐藏其含义。

本次 Windows 环境为 Microsoft YaHei；其他平台可选择已安装的可读中文字体。`render.ps1` 使用 UTF-8 BOM，以免 Windows PowerShell 错读中文文件名。

在项目目录运行，保持相对 ASCII 输出目录 `media`。本次 TeX 工具对中文绝对输出路径有兼容问题，不把 `media_dir` 改为中文绝对路径。`media/Tex/*.tex` 是自动生成的缓存，应修改上游公式源码。

## 中文与数学混排

- `eq()` 使用 `MathTex`；中文 `cn()` 中的 `$...$` 片段也使用 `MathTex`，普通中文采用 `Text`。
- 将 `J_f`、`J_d`、单位向量、坐标、叉乘、正负方向写成 LaTeX，不能在屏幕上露出源码下划线。
- 偏导采用 `\frac{\partial\mathbf D}{\partial t}` 等分式；避免未定义的 `\partial_t`、`\partial_z` 缩略写法。
- 混排需统一基线，尤其是仅有“，”“、”“：”的文字片段；简单按包围盒居中会使标点偏高。模板使用临时参考字形对齐基线，再移除参考字形。
- 分行时把整段数学表达视为不可拆分单元。不要用字符数截断 LaTeX 命令、下标或公式。
- `narration.json` 的 `latex_text` 是画面排版文本，可含 `$...$` 和明确换行；`text` 是播放器可读的纯文字字幕。导出 SRT 不直接复制原始 LaTeX 源码。
- 数学字号与中文字号不必数值相同，实际字高、分式高度和可读性更重要。确认下标、帽子、分式及标点在 1080p 实际帧中可辨认。

## 命令

模板 `render.ps1` 优先使用显式 `-Python`；未指定时尝试本工作区两层上方的 `.venv`，再回退到 `python`。其他平台可直接运行 Python 命令。

```powershell
# 替换为实际环境中的 Python 路径。
powershell -NoProfile -ExecutionPolicy Bypass -File .\render.ps1 `
  -Python 'D:\code\uv\.venv\Scripts\python.exe' `
  -OutputName '梯度_散度_旋度_修正版_v4.mp4'

$env:LESSON_CHAPTER = 'electromagnetism'
& 'D:\code\uv\.venv\Scripts\python.exe' verify_video.py --stills
Remove-Item Env:\LESSON_CHAPTER
```

`-Draft` 用于低分辨率预览。单章预览后的环境变量必须清除，再渲染全片。

对应的跨平台步骤为：

```text
python -m manim --resolution 1920,1080 --fps 24 vector_calculus.py VectorCalculus -o lesson
python make_bgm.py --video media/videos/vector_calculus/1080p24/lesson.mp4 --output media/videos/vector_calculus/1080p24/lesson_bgm.mp4
python -m manim -s vector_calculus.py Cover
python verify_video.py --video media/videos/vector_calculus/1080p24/lesson_bgm.mp4
```

## 有针对性的验收

1. 静帧：检查标题、成员、字幕行数、公式、下标、曲面积分闭合圈、中文标点、边界裁切、遮挡和图像密度。
2. 运动：在固定标题、公式和字幕以外的图像区域比较多个时刻，确认实际运动；检查分镜交界处轨迹连续。
3. 梯度：曲面点满足 `z=x²+2y²`；箭头起点贴合点；提升切向与曲面法向点积为零；标签保持相对位置。再在视频帧中检测标签实际出现的位置，避免只检查源数据。
4. 波场：数值检查 `E·H=0`、纵向分量为零、同相和 `E×H` 传播方向。截图检查它们确实画在两张正交平面中。
5. 成片：分辨率、帧率、总时长、22 段实例时间线、完整字幕、纯黑背景、H.264 视频与单条 AAC BGM 音轨、音量和淡入淡出。

原实例验证了约 367 个梯度实际帧和 697 对波场向量。数字是本次片长和采样密度的结果，不作为其他作业的硬编码门槛。新主题应调整检查，使其验证实际模型，不能盲目复用不存在的梯度场景测试。

分镜检查不会覆盖正式成片的帧精确时间线。BGM 根据实际视频长度生成，封装时复制原视频数据。普通 Manim 命令只生成无配乐画面，不能误当作最后交付视频。

## 修订交付与旧文件占用

使用独立的新文件名导出修订，并对那个文件执行检查。同步旧别名属于兼容步骤；遇到被播放器占用的旧文件，可报告未覆盖，但不能因此中断新文件的验证。不要关闭用户应用。

本实例曾出现旧“入门版”被占用，导致用户继续看到 `J_f`、`J_d` 原样下划线。排查时比较文件修改时间、哈希和实际截图，不能仅归因于 LaTeX 编译失败，也不能未核对就断言用户看错版本。

交付最新版 MP4 的明确链接、必要的成片核对截图和检查结果；不要宣称仍被占用的旧文件已经同步。引用书目、字幕和源文件也应与当前交付内容一致。
