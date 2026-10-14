# 数学与电磁学图像约定

## 梯度与真实曲面

本例函数为

\[
z=f(x,y)=x^2+2y^2,\qquad \nabla_{xy}f=(2x,4y).
\]

画实际三维椭圆抛物面，不能仅画若干平面椭圆并暗示曲面高度。等高线可参数化为

\[
(x,y,z)=\left(r\cos\theta,\frac{r}{\sqrt2}\sin\theta,r^2\right).
\]

正交投影使用一致的 xyz 比例。梯度在 xy 平面指向最快增加方向，是非零梯度处等值线的法向。曲面箭头表示这一方向在函数图像上的上升切向，并非抛物面法向。

若单位方向为 \(\hat{\mathbf u}=(u_x,u_y)\)，其曲面提升切向为

\[
\left(u_x,u_y,\nabla_{xy}f\cdot\hat{\mathbf u}\right),
\qquad D_{\hat{\mathbf u}}f=\nabla_{xy}f\cdot\hat{\mathbf u}.
\]

移动点满足曲面方程；箭头起点绑定该点，标签绑定箭头端点并维持固定屏幕间距。跨三个梯度分镜保持轨迹连续。不要留下 xy 底面投影的旧梯度标签，让它被误认为曲面箭头的标识。

## 通量与散度

法向约定取外法向。闭合曲面 \(S\) 包围区域 \(V\)，用闭合曲面积分写

\[
\nabla\cdot\mathbf F=\lim_{|V|\to0}\frac1{|V|}
\oiint_S\mathbf F\cdot\hat{\mathbf n}\,\mathrm dS.
\]

在说明中定义 \(S\) 和 \(V\)。本作业采用 \(\oiint_S\) 代替将 \(\partial V\) 直接用作积分下标的写法，以免初学者把“区域边界”记号误认为偏导。

对电位移矢量：

\[
\nabla\cdot\mathbf D=\rho_f,\qquad
\oiint_S\mathbf D\cdot\hat{\mathbf n}\,\mathrm dS=Q_f.
\]

注明 \(S\) 为闭合高斯面，\(Q_f\) 为所围自由电荷。二维圆形图像是球形区域和高斯面的截面示意；不要把二维场线数量当作三维通量的精确测量。

## 环量与旋度

\(C\) 为闭合边界曲线，\(C=\partial S\)，\(\Delta S\) 为所围面积：

\[
(\nabla\times\mathbf F)\cdot\hat{\mathbf n}
=\lim_{\Delta S\to0}\frac1{\Delta S}
\oint_C\mathbf F\cdot\mathrm d\mathbf l.
\]

曲线正向绕行与法向遵循右手定则。不要在未经说明时只写积分下标 \(\partial S\)。该记号本身表示曲面边界，不是偏导数。

平面例子仅在 \(F_z=0\)、\(\frac{\partial\mathbf F}{\partial z}=\mathbf0\) 时使用

\[
(\nabla\times\mathbf F)_z=
\frac{\partial F_y}{\partial x}-\frac{\partial F_x}{\partial y}.
\]

本例比较 \((x,y)\)、\((-y,x)\)、\((x-y,x+y)\)，其散度和旋度 z 分量分别为 \((2,0)\)、\((0,2)\)、\((2,2)\)。全局环量与某处局部旋度不能混为一谈。

## 课程物理例子

- 静电场：\(\mathbf E=-\nabla\varphi\)，指向电势降低；不得泛化到任意时变电场。
- 稳恒长直导线：\(\nabla\times\mathbf H=\mathbf J_f\)，且 \(\frac{\partial\mathbf D}{\partial t}=\mathbf0\)。导线外无电流处局部旋度为零，但围住导线的环路仍可有非零环量。
- 充电电容：\(\nabla\times\mathbf H=\mathbf J_f+\frac{\partial\mathbf D}{\partial t}\)，极板间 \(\mathbf J_f=\mathbf0\)；忽略边缘效应。
- \(\mathbf D\) 是电位移矢量，位移电流密度是 \(\mathbf J_d=\frac{\partial\mathbf D}{\partial t}\)。不得将 \(\mathbf D\) 直接称为“位移电流”。

## 平面波方向与相位

场景限定在均匀、各向同性、无损线性介质中无自由源的平面波。取沿 +x 传播：

\[
\mathbf E=(0,E_0\sin(kx-\omega t),0),\quad
\mathbf H=(0,0,H_0\sin(kx-\omega t)).
\]

\(\mathbf E\perp\mathbf H\)，两者均垂直于传播方向；它们同相，\(\mathbf E\times\mathbf H\) 沿 +x。电场在 xy 平面振荡，磁场在 xz 平面振荡。二维投影下的斜线仍可对应三维中的正交矢量。

并列的同相正弦曲线只表示分量随位置变化，不能单凭这种图像表达空间正交。本模板采用共享传播轴的三维投影。两种场的图示幅值分别归一化，不能比较屏幕长度来推断物理幅值或波阻抗。

\(\mathbf E\perp\mathbf H\) 是该平面波场景的结论，不能作为所有静态场、近场或任意场分布的通用断言。
