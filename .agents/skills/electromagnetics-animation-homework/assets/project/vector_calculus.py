"""Mathematical animation with full on-screen explanations.

Pure black; dynamic geometry, mathematical morphs, and electromagnetic examples.
render.ps1 adds an original instrumental background track without narration.
Run render.ps1 in this directory. LESSON_CHAPTER selects a chapter preview.
"""
from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path

import numpy as np
from manim import *

ROOT=Path(__file__).resolve().parent
BG="#000000"
INK="#eeeeee"
MUTED="#999999"
LINE="#777777"
ACCENT="#8db7c5"
FONT="Microsoft YaHei"
LEFT_CENTER=np.array([-3.25,.25,0])
RIGHT_CENTER=np.array([3.35,.25,0])
PROJECT_TITLE="电磁场与电磁波理论第一章动画作业"
PROJECT_SUBTITLE="梯度 散度 旋度 介绍"
MEMBERS="B24010722 B24010723 B24010724 B24010725"
CLOSED_SURFACE_TEX=TexTemplate()
CLOSED_SURFACE_TEX.add_to_preamble(r"\usepackage{esint}")


def cn(text,size=27,color=INK,width=6):
    # Chinese prose uses Text; $...$ spans use MathTex, including in subtitles.
    if "$" in text:
        rows=[]
        for line in text.split("\n"):
            parts=[]
            cursor=0.
            for span in re.split(r"(\$[^$\n]+\$)",line):
                if not span: continue
                # A temporary full-height glyph supplies a common baseline even
                # when a prose span contains only a comma or an ideographic comma.
                if span.startswith("$"):
                    anchored=MathTex(r"\mathrm{H}",span[1:-1],arg_separator="",
                                     font_size=size*1.4,color=color)
                    part=anchored[1]
                else:
                    anchored=Text("中"+span,font=FONT,font_size=size,color=color)
                    part=VGroup(*anchored[1:])
                part.shift(DOWN*anchored[0].get_center()[1])
                part.shift(RIGHT*(cursor-part.get_left()[0]))
                cursor+=part.width+.04
                parts.append(part)
            rows.append(VGroup(*parts).center())
        obj=VGroup(*rows).arrange(DOWN,aligned_edge=LEFT,buff=.13*size/24)
    else:
        obj=Text(text,font=FONT,font_size=size,color=color,line_spacing=.9)
    if obj.width>width: obj.scale_to_fit_width(width)
    return obj


def eq(tex,size=38,color=INK,width=6):
    options={"tex_template":CLOSED_SURFACE_TEX} if r"\oiint" in tex else {}
    obj=MathTex(tex,font_size=size,color=color,**options)
    if obj.width>width: obj.scale_to_fit_width(width)
    return obj


def panel(*objects,center=RIGHT_CENTER,gap=.48):
    return VGroup(*objects).arrange(DOWN,buff=gap).move_to(center)


def title_card():
    return VGroup(cn(PROJECT_TITLE,44,width=12.6).move_to([0,1.65,0]),
                  cn(PROJECT_SUBTITLE,35,width=12.6).move_to([0,.3,0]),
                  cn("组内成员",24,MUTED).move_to([0,-1.15,0]),
                  cn(MEMBERS,20,width=10.5).move_to([0,-1.9,0]))


def paraboloid_figure():
    """Orthographic view of the actual graph z=x²+2y², with equal xyz scale."""
    azimuth=-PI/4; elevation=40*DEGREES; scale=1.15
    origin=LEFT_CENTER+DOWN*1.55
    c,s=math.cos(azimuth),math.sin(azimuth)
    e,k=math.sin(elevation),math.cos(elevation)
    view=np.array([[c,-s,0],[e*s,e*c,k],[-k*s,-k*c,e]])
    def project(point):
        return origin+scale*(view@np.array(point,dtype=float))
    def screen(point):
        p=project(point); p[2]=0
        return p
    def graph(r,t):
        return np.array([r*math.cos(t),r/math.sqrt(2)*math.sin(t),r*r])
    radius=1.75
    surface=Surface(lambda r,t:project(graph(r,t)),u_range=(0,radius),v_range=(0,TAU),
                    resolution=(12,36),fill_color=LINE,fill_opacity=.09,
                    checkerboard_colors=False,stroke_width=0)
    surface.set_shade_in_3d(False)
    surface.submobjects.sort(key=lambda face:face.get_center()[2])
    mesh=VGroup(*(ParametricFunction(lambda r,t=t:project(graph(r,t)),t_range=(0,radius),
                                    color=LINE,stroke_width=1.0) for t in np.linspace(0,TAU,12,endpoint=False)))
    levels=VGroup(*(ParametricFunction(lambda t,r=r:project(graph(r,t)),t_range=(0,TAU),
                                      color=MUTED,stroke_width=1.1) for r in [.4,.8,1.15,1.5,radius]))
    axes=VGroup()
    for name,end in [("x",[2.05,0,0]),("y",[0,1.55,0]),("z",[0,0,3.35])]:
        arrow=Arrow(screen([0,0,0]),screen(end),buff=0,color=LINE,stroke_width=1.2,
                    max_tip_length_to_length_ratio=.055)
        label=eq(name,22,MUTED).next_to(arrow.get_end(),{"x":RIGHT,"y":LEFT,"z":UP}[name],buff=.10)
        axes.add(arrow,label)
    static=VGroup(axes,surface,mesh,levels,
                  eq(r"z=f(x,y)=x^2+2y^2",28).move_to([-3.25,-2.7,0]))
    return static,screen,graph


def plane_wave_vectors(x,phase):
    """Normalized +x plane wave: E along y, H along z, with equal phase."""
    q=np.sin(2.3*np.asarray(x)-phase)
    zero=np.zeros_like(q)
    return np.stack([zero,q,zero],axis=-1),np.stack([zero,zero,q],axis=-1)


def transverse_wave_figure():
    """Project perpendicular xy/xz wave planes through one shared x axis."""
    c=.86; s=-math.sqrt(1-c*c); e=-.5; k=math.sqrt(1-e*e)
    view=np.array([[c,0,s],[-e*s,k,e*c],[-k*s,-e,k*c]])
    center=LEFT_CENTER+UP*.1
    def project(point):
        p=center+view@np.asarray(point,dtype=float); p[2]=0
        return p
    planes=VGroup()
    for axis in [1,2]:
        corners=[]
        for x,a in [(-2.2,-.85),(2.2,-.85),(2.2,.85),(-2.2,.85)]:
            p=np.array([x,0.,0.]);p[axis]=a;corners.append(project(p))
        planes.add(Polygon(*corners,color=LINE,stroke_width=.6,fill_color=LINE,fill_opacity=.035))
    origin=np.array([-2.35,0,0])
    axes=VGroup()
    for text,end,color in [(r"+x",[2.6,0,0],MUTED),
                           (r"E_y\;(y)",[-2.35,1.15,0],ACCENT),
                           (r"H_z\;(z)",[-2.35,0,1.05],INK)]:
        axis=Arrow(project(origin),project(end),buff=0,color=LINE,stroke_width=1.3,
                   max_tip_length_to_length_ratio=.06)
        label=eq(text,25,color).next_to(axis.get_end(),LEFT if text!=r"+x" else DOWN,buff=.12)
        axes.add(axis,label)
    curves=VGroup(VMobject(color=ACCENT,stroke_width=2.4),VMobject(color=INK,stroke_width=2.1))
    seeds=np.linspace(-2.12,2.12,19)
    ribs=VGroup()
    for x in seeds:
        for axis,color in [(1,ACCENT),(2,INK)]:
            end=np.array([x,0.,0.]);end[axis]=.2
            ribs.add(Arrow(project([x,0,0]),project(end),buff=0,color=color,stroke_width=1.05,
                           max_tip_length_to_length_ratio=.16))
    moving=VGroup(curves,ribs)
    figure=VGroup(planes,axes,moving,
                  cn("均匀各向同性无损介质",19,MUTED).move_to([-3.25,-1.85,0]),
                  cn(r"$\mathbf E$、$\mathbf H$ 幅值分别归一化",19,MUTED).move_to([-3.25,-2.25,0]))
    samples=np.linspace(-2.2,2.2,100)
    def update(phase):
        electric,magnetic=plane_wave_vectors(samples,phase)
        for curve,values in zip(curves,[electric,magnetic]):
            curve.set_points_smoothly([project(np.array([x,0,0])+.78*v) for x,v in zip(samples,values)])
        electric,magnetic=plane_wave_vectors(seeds,phase)
        for index,x in enumerate(seeds):
            for offset,values in enumerate([electric,magnetic]):
                arrow=ribs[2*index+offset];v=values[index];magnitude=np.linalg.norm(v)
                if magnitude>1e-5:
                    arrow.put_start_and_end_on(project([x,0,0]),project(np.array([x,0,0])+.78*v))
                arrow.set_opacity(min(1.,magnitude/.08))
    update(0)
    return figure,moving,update


def field(func,center=LEFT_CENTER,extent=(2.1,1.4),step=.7,color=MUTED,scale=.24,radial_limit=None):
    arrows=VGroup()
    seeds=[]
    nx=int(extent[0]/step+1e-6); ny=int(extent[1]/step+1e-6)
    for x in np.arange(-nx,nx+1)*step:
        for y in np.arange(-ny,ny+1)*step:
            v=np.array([*func(x,y),0.],dtype=float)
            norm=np.linalg.norm(v)
            if norm<1e-7: continue
            if radial_limit and math.hypot(x,y)>radial_limit: continue
            v*=min(scale,.49/norm)
            p=center+[x,y,0]
            arrows.add(Arrow(p,p+v,buff=0,color=color,stroke_width=1.5,
                             max_tip_length_to_length_ratio=.23))
            seeds.append(np.array([x,y,0.]))
    arrows.flow_seeds=seeds
    arrows.flow_center=np.array(center,dtype=float)
    return arrows


def flow_motion(arrows,kind,seconds):
    """Advect existing field arrows along analytical streamlines; no particles."""
    seeds=arrows.flow_seeds
    center=arrows.flow_center
    def update(group,alpha):
        for index,(arrow,seed) in enumerate(zip(group,seeds)):
            phase=(alpha*seconds*.17+index*.173)%1
            if kind=="uniform":
                position=seed+np.array([1.1*(phase-.5),0,0]); vector=np.array([1.,0,0])
            else:
                sign=1 if kind=="source" else -1
                position=seed*math.exp(sign*.5*(phase-.5)); vector=sign*position
            length=np.linalg.norm(vector)
            delta=vector*min(.24,.49/max(length,1e-8))
            arrow.put_start_and_end_on(center+position,center+position+delta)
            arrow.set_opacity(.12+.88*math.sin(PI*phase)**2)
    return UpdateFromAlphaFunc(arrows,update)


def panel_change(source,target):
    if isinstance(source[0],MathTex) and isinstance(target[0],MathTex):
        return [TransformMatchingShapes(source[0],target[0]),
                FadeOut(VGroup(*source[1:])),FadeIn(VGroup(*target[1:]))]
    return [FadeTransform(source,target)]


def stamp(seconds):
    ms=round(seconds*1000)
    return f"{ms//3600000:02d}:{ms//60000%60:02d}:{ms//1000%60:02d},{ms%1000:03d}"


def subtitle_lines(text,limit=40):
    lines=[]; current=""
    for clause in re.findall(r"[^，。；！？]+[，。；！？]?",text):
        if current and len(current)+len(clause)>limit:
            lines.append(current); current=""
        while len(clause)>limit:
            lines.append(clause[:limit]); clause=clause[limit:]
        current+=clause
    if current: lines.append(current)
    return "\n".join(lines)


class VectorCalculus(Scene):
    def construct(self):
        self.camera.background_color=BG
        items=json.loads((ROOT/"narration.json").read_text("utf-8"))
        self.lines={item["id"]:item for item in items}
        self.timeline=[]
        self.gradient_trace=[]
        self.heading=None
        self.caption=None
        self.pending=[]
        chapters=["opening","intro","gradient","divergence","curl","comparison","electromagnetism","recap","references"]
        only=os.environ.get("LESSON_CHAPTER")
        if only and only not in chapters: raise ValueError(only)
        for chapter in chapters:
            if not only or only==chapter: getattr(self,chapter)()
        self.wait(.12)
        self.write_timeline(only or "full")

    def header(self,title):
        heading=cn(title,33,width=12.5).to_edge(UP,buff=.42).to_edge(LEFT,buff=.65)
        self.pending.append(AnimationGroup(FadeOut(self.heading,shift=UP*.12),
                                           FadeIn(heading,shift=DOWN*.12),lag_ratio=.75)
                            if self.heading else FadeIn(heading))
        self.heading=heading

    def clear_stage(self,keep=()):
        retained={id(m) for obj in keep for m in obj.get_family()}
        for obj in list(self.mobjects):
            if obj not in [self.heading,self.caption] and id(obj) not in retained:
                self.pending.append(FadeOut(obj,shift=UP*.12))

    def say(self,key,*animations,run_time=.72,motion=None,motion_kind=None,transition=None,display_subtitle=True):
        item=self.lines[key]
        duration=float(item["seconds"])
        start=self.time
        if self.caption: self.remove(self.caption)
        subtitle=subtitle_lines(item["text"])
        self.caption=None
        if display_subtitle:
            self.caption=cn(item.get("latex_text",subtitle),24,INK,width=12.8).move_to([0,-3.38,0])
            if self.caption.height>.95: self.caption.scale_to_fit_height(.95)
            self.add(self.caption)
        entries=self.pending+list(animations)
        self.pending=[]
        if entries: self.play(*entries,run_time=min(run_time,duration))
        motion_start=self.time
        remaining=duration-(self.time-start)
        if remaining>0:
            if motion: self.play(*motion(remaining),run_time=remaining,rate_func=linear)
            else: self.wait(remaining)
        self.timeline.append({"id":key,"start":start,"planned_seconds":duration,
                              "end":self.time,"text":item["text"],"subtitle":subtitle,
                              "caption":item["caption"],
                              "presentation":"subtitle" if display_subtitle else "card",
                              "motion_kind":motion_kind,"motion_start":motion_start if motion else None,
                              "transition":transition,"transition_seconds":motion_start-start})

    def write_timeline(self,name):
        folder=ROOT/"output"
        folder.mkdir(exist_ok=True)
        (folder/f"timeline_{name}.json").write_text(json.dumps(self.timeline,ensure_ascii=False,indent=2),"utf-8")
        entries=[]
        for segment in self.timeline:
            entries.append(f"{len(entries)+1}\n{stamp(segment['start'])} --> {stamp(segment['end'])}\n{segment['subtitle']}\n")
        (folder/f"lesson_{name}.srt").write_text("\n".join(entries),"utf-8-sig")
        if self.gradient_trace:
            qa=ROOT/"qa"; qa.mkdir(exist_ok=True)
            (qa/f"gradient_track_{name}.json").write_text(
                json.dumps(self.gradient_trace,ensure_ascii=False,indent=2),"utf-8")

    def opening(self):
        self.say("opening",FadeIn(title_card(),shift=UP*.1),run_time=.65,
                 transition="opening-title-card",display_subtitle=False)

    def intro(self):
        self.clear_stage()
        self.header("场的微分运算")
        scalar=panel(cn("标量场",30),eq(r"f:\mathbb R^3\to\mathbb R",44),
                     cn("每个位置对应一个数",24,MUTED),center=[-3.5,.4,0])
        vector=panel(cn("矢量场",30),eq(r"\mathbf F:\mathbb R^3\to\mathbb R^3",44),
                     cn("每个位置对应一个矢量",24,MUTED),center=[3.5,.4,0])
        self.say("fields",FadeIn(scalar),FadeIn(vector))
        self.clear_stage(keep=(scalar,vector))
        columns=VGroup()
        for x,title,formula,kind in [(-4.3,"梯度",r"\nabla f",r"标量 $\to$ 矢量"),
                                     (0,"散度",r"\nabla\cdot\mathbf F",r"矢量 $\to$ 标量"),
                                     (4.3,"旋度",r"\nabla\times\mathbf F",r"矢量 $\to$ 矢量")]:
            columns.add(panel(cn(title,30),eq(formula,46),cn(kind,24,MUTED),center=[x,.35,0]))
        self.say("overview",FadeTransform(VGroup(scalar,vector),columns),
                 run_time=.95,transition="field-types-to-operators")
        self.overview_columns=columns

    def gradient(self):
        columns=getattr(self,"overview_columns",None)
        self.clear_stage(keep=(columns,) if columns else ()); self.header("梯度与方向导数")
        static,project,graph=paraboloid_figure()
        local=[graph(1.15,math.atan(math.sqrt(2)))]
        p=project(local[0])
        point=Dot(p,radius=.04,color=INK)
        grad=Arrow(p,p+UP*.7,buff=0,color=ACCENT,stroke_width=2.8)
        label=VGroup(eq(r"\nabla_{xy}f",23,ACCENT),cn("对应上升切向",17,ACCENT,width=2))
        label.arrange(DOWN,buff=.07)
        moving=VGroup(point,grad,label)
        figure=VGroup(static,moving)
        explanation=panel(cn("椭圆抛物面",30),eq(r"\nabla_{xy}f=(2x,4y)",36),
                          cn(r"梯度：$xy$ 平面的最快增加方向",23,MUTED),
                          cn("曲面箭头：沿梯度方向抬升",23,MUTED),
                          eq(r"\max_{|\hat{\mathbf u}|=1}D_{\hat{\mathbf u}}f=|\nabla f|",35))
        def update_gradient(angle,phase=None):
            local[0]=graph(1.15,angle)
            x,y,z=local[0]; g=np.array([2*x,4*y]); u=g/np.linalg.norm(g)
            p=project([x,y,z])
            point.move_to(p)
            lifted=np.array([*u,np.dot(g,u)])
            grad.put_start_and_end_on(p,project(local[0]+.27*lifted))
            label.next_to(grad.get_end(),RIGHT,buff=.14)
            if phase:
                self.gradient_trace.append({"phase":phase,"seconds":self.time,"angle":angle,
                    "world_point":local[0].tolist(),"world_tangent":lifted.tolist(),
                    "point":point.get_center().tolist(),"arrow_start":grad.get_start().tolist(),
                    "arrow_end":grad.get_end().tolist(),"label_left":label.get_left().tolist(),
                    "label_bounds":[label.get_left()[0],label.get_bottom()[1],
                                    label.get_right()[0],label.get_top()[1]]})
        update_gradient(math.atan(math.sqrt(2)))
        def gradient_motion(start_angle,end_angle,phase):
            def factory(seconds):
                def update(group,alpha):
                    angle=start_angle+(end_angle-start_angle)*alpha
                    update_gradient(angle,phase)
                return [UpdateFromAlphaFunc(moving,update)]
            return factory
        if columns:
            entering=[FadeOut(columns),FadeIn(static),FadeIn(VGroup(point,grad,label[1])),
                      TransformMatchingTex(columns[0][1].copy(),label[0])]
        else: entering=[FadeIn(figure)]
        self.say("grad_geometry",*entering,FadeIn(explanation),run_time=.95,
                 motion=gradient_motion(math.atan(math.sqrt(2)),1.45,"grad_geometry"),
                 motion_kind="gradient-and-lifted-tangent-on-paraboloid",transition="gradient-symbol-to-paraboloid")
        directional=panel(eq(r"D_{\hat{\mathbf u}}f=\nabla f\cdot\hat{\mathbf u}",39),
                          eq(r"=|\nabla f|\cos\theta",39),cn(r"单位方向：$|\hat{\mathbf u}|=1$",23,MUTED))
        unit=Arrow(point.get_center(),point.get_center()+LEFT*.4,buff=0,color=INK,stroke_width=1.8,
                   max_tip_length_to_length_ratio=.19)
        unit_label=cn(r"$\hat{\mathbf u}$ 方向切向",17,INK,width=2)
        unit_pair=VGroup(unit,unit_label)
        def update_direction(alpha,phase=None):
            update_gradient(1.45+.45*alpha,phase)
            x,y,z=local[0]; g=np.array([2*x,4*y])
            angle=math.atan2(g[1],g[0])+PI/2*math.cos(TAU*alpha)
            u=np.array([math.cos(angle),math.sin(angle)])
            unit.put_start_and_end_on(project(local[0]),project(local[0]+.27*np.array([*u,np.dot(g,u)])))
            unit_label.next_to(point.get_center(),LEFT,buff=.2).shift(DOWN*.28)
        update_direction(0)
        def direction_motion(seconds):
            def update(group,alpha):
                update_direction(alpha,"grad_directional")
            return [UpdateFromAlphaFunc(VGroup(moving,unit_pair),update)]
        self.say("grad_directional",FadeTransform(explanation,directional),FadeIn(unit_pair),
                 motion=direction_motion,motion_kind="moving-point-with-directional-tangent",
                 transition="geometric-gradient-to-directional-derivative")
        definition=panel(eq(r"\nabla_{xy}f=(2x,4y)",38),
                         eq(r"\nabla f=\left(\frac{\partial f}{\partial x},\frac{\partial f}{\partial y},\frac{\partial f}{\partial z}\right)",30),
                         cn("二维本例；三维一般形式",23,MUTED))
        self.say("grad_formula",*panel_change(directional,definition),FadeOut(unit_pair),
                 motion=gradient_motion(1.90,2.35,"grad_formula"),motion_kind="gradient-and-lifted-tangent-on-paraboloid",
                 transition="matching-gradient-formulas")
        self.gradient_figure=figure
        self.gradient_panel=definition

    def divergence(self):
        old_figure=getattr(self,"gradient_figure",None)
        old_panel=getattr(self,"gradient_panel",None)
        self.clear_stage(keep=tuple(x for x in [old_figure,old_panel] if x is not None))
        self.header("通量与散度")
        arrows=field(lambda x,y:(x,y),extent=(1.4,1.4),radial_limit=1.7)
        boundary=Square(side_length=1.2,color=ACCENT,stroke_width=1.6).move_to(LEFT_CENTER)
        normal=Arrow(LEFT_CENTER+[.6,.05,0],LEFT_CENTER+[1.12,.05,0],buff=0,
                     color=ACCENT,stroke_width=2,max_tip_length_to_length_ratio=.17)
        normal_label=eq(r"\hat{\mathbf n}",26,ACCENT).next_to(normal,UP,buff=.12)
        figure=VGroup(arrows,boundary,normal,normal_label,
                      cn("二维截面示意",20,MUTED).move_to([-3.25,-2.15,0]))
        flux=panel(eq(r"\Phi=\iint_S\mathbf F\cdot\hat{\mathbf n}\,dS",40),
                   cn("外法向为正",25,MUTED))
        entering=[FadeTransform(old_figure,figure),FadeTransform(old_panel,flux)] if old_figure else [FadeIn(figure),FadeIn(flux)]
        self.say("div_flux",*entering,run_time=.95,
                 motion=lambda seconds:[flow_motion(arrows,"source",seconds)],
                 motion_kind="outward-field-advection",transition="contours-to-vector-field-and-flux")
        self.clear_stage(keep=(figure,flux))
        cases=VGroup()
        case_fields=[]
        for x,func,sign in [(-4.3,lambda x,y:(x,y),r"\nabla\cdot\mathbf F>0"),
                            (0,lambda x,y:(-x,-y),r"\nabla\cdot\mathbf F<0"),
                            (4.3,lambda x,y:(1,0),r"\nabla\cdot\mathbf F=0")]:
            center=np.array([x,.75,0])
            case_field=field(func,center,extent=(1.3,1.05),step=.65)
            case_fields.append(case_field)
            cases.add(VGroup(case_field,
                      Square(side_length=.85,color=LINE,stroke_width=1.2).move_to(center),
                      eq(sign,32,width=3.7).move_to([x,-1.35,0])))
        self.curl_seed=case_fields[0].copy()
        self.say("div_cases",FadeTransform(figure,cases[0]),FadeOut(flux),
                 LaggedStart(FadeIn(cases[1]),FadeIn(cases[2]),lag_ratio=.15),run_time=.95,
                 motion=lambda seconds:[flow_motion(f,kind,seconds) for f,kind in zip(case_fields,["source","sink","uniform"])],
                 motion_kind="source-sink-uniform-flow",transition="single-field-to-three-flux-cases")
        self.clear_stage()
        definition=panel(eq(r"\nabla\cdot\mathbf F=\lim_{|V|\to0}\frac{1}{|V|}\oiint_S\mathbf F\cdot\hat{\mathbf n}\,\mathrm dS",45,width=11.8),
                         cn(r"闭合曲面 $S$ 包围体积 $V$，取单位体积的净向外通量",24,MUTED,width=11.8),center=[0,.45,0])
        self.say("div_definition",FadeIn(definition,shift=DOWN*.12),run_time=.85,
                 transition="field-cases-to-local-flux-limit")
        cartesian=panel(eq(r"\nabla\cdot\mathbf F=\frac{\partial F_x}{\partial x}+\frac{\partial F_y}{\partial y}+\frac{\partial F_z}{\partial z}",44,width=11.8),
                        cn(r"矢量场 $\to$ 标量场",26,MUTED),center=[0,.45,0])
        self.say("div_formula",*panel_change(definition,cartesian),run_time=.9,
                 transition="matching-divergence-integral-and-derivative")

    def curl(self):
        self.clear_stage(); self.header("环量与旋度")
        arrows=field(lambda x,y:(-y,x),extent=(1.4,1.4),radial_limit=1.7)
        loop=Circle(radius=1.04,color=ACCENT,stroke_width=1.6).move_to(LEFT_CENTER)
        tangent=Arrow(LEFT_CENTER+[1.04,0,0],LEFT_CENTER+[1.04,.55,0],buff=0,
                      color=ACCENT,stroke_width=2.3,max_tip_length_to_length_ratio=.19)
        tangent_label=eq(r"d\mathbf l",26,ACCENT).next_to(tangent,RIGHT,buff=.13)
        figure=VGroup(arrows,loop,tangent,tangent_label,
                      eq(r"\mathbf F=(-y,x)",29).move_to([-3.25,-2.15,0]))
        circulation=panel(eq(r"\Gamma=\oint_C\mathbf F\cdot d\mathbf l",42),
                          cn("闭合曲线的切向贡献",25,MUTED))
        self.curl_angle=0.
        def curl_motion(seconds):
            start_angle=self.curl_angle
            angular_speed=TAU/6
            self.curl_angle+=angular_speed*seconds
            radius=loop.width/2
            def update(group,alpha):
                angle=start_angle+angular_speed*seconds*alpha
                rot=np.array([[math.cos(angle),-math.sin(angle),0],
                              [math.sin(angle),math.cos(angle),0],[0,0,1]])
                for arrow,seed in zip(arrows,arrows.flow_seeds):
                    local=rot@seed
                    vector=np.array([-local[1],local[0],0.])*.24
                    arrow.put_start_and_end_on(LEFT_CENTER+local,LEFT_CENTER+local+vector)
                local=radius*np.array([math.cos(angle),math.sin(angle),0.])
                delta=radius*.5*np.array([-math.sin(angle),math.cos(angle),0.])
                tangent.put_start_and_end_on(LEFT_CENTER+local,LEFT_CENTER+local+delta)
                tangent_label.move_to(LEFT_CENTER+(radius+.28)*np.array([math.cos(angle),math.sin(angle),0.])+UP*.1)
            return [UpdateFromAlphaFunc(figure,update)]
        seed=getattr(self,"curl_seed",None)
        if seed is not None:
            seed=seed.copy().shift(LEFT_CENTER-seed.flow_center)
        else: seed=field(lambda x,y:(x,y),extent=(1.4,1.4),radial_limit=1.7)
        self.say("curl_loop",ReplacementTransform(seed,arrows,path_arc=PI/8),
                 FadeIn(VGroup(loop,tangent,tangent_label,figure[-1])),FadeIn(circulation),run_time=1.0,
                 motion=curl_motion,motion_kind="tangential-vector-and-field-circulation",
                 transition="radial-vector-field-to-circulating-field")
        limit=panel(eq(r"(\nabla\times\mathbf F)\cdot\hat{\mathbf n}",36),
                    eq(r"=\lim_{\Delta S\to0}\frac{1}{\Delta S}\oint_C\mathbf F\cdot d\mathbf l",34),
                    cn(r"$C=\partial S$：闭合边界；$\Delta S$：所围面积",21,MUTED))
        self.say("curl_definition",*panel_change(circulation,limit),loop.animate.scale(.62),run_time=.9,
                 motion=curl_motion,motion_kind="circulation-around-shrinking-loop",
                 transition="matching-circulation-to-curl-limit")
        directions=panel(cn("右手定则",29),cn(r"逆时针 $\to +z$",28),cn(r"顺时针 $\to -z$",28))
        self.say("curl_direction",FadeTransform(limit,directions),
                 motion=curl_motion,motion_kind="oriented-loop-and-right-hand-normal",
                 transition="curl-limit-to-orientation-convention")
        cartesian=panel(eq(r"(\nabla\times\mathbf F)_z=\frac{\partial F_y}{\partial x}-\frac{\partial F_x}{\partial y}",36),
                        eq(r"F_z=0,\quad\frac{\partial\mathbf F}{\partial z}=\mathbf0",32,MUTED),
                        cn("平面场仅有法向分量",24,MUTED))
        self.say("curl_formula",FadeTransform(directions,cartesian),
                 motion=curl_motion,motion_kind="tangential-vector-and-field-circulation",
                 transition="geometric-curl-to-coordinate-formula")
        self.curl_figure=figure
        self.curl_panel=cartesian

    def comparison(self):
        old_figure=getattr(self,"curl_figure",None)
        old_panel=getattr(self,"curl_panel",None)
        self.clear_stage(keep=tuple(x for x in [old_figure,old_panel] if x is not None))
        self.header("散度与旋度的比较")
        table=VGroup()
        table.add(cn("矢量场",26,MUTED).move_to([-3.9,1.95,0]),
                  cn("散度",26,MUTED).move_to([.4,1.95,0]),
                  cn(r"旋度的 $z$ 分量",26,MUTED).move_to([4.15,1.95,0]))
        for y,tex,div,curl in [(1,r"(x,y)","2","0"),(0,r"(-y,x)","0","2"),
                               (-1,r"(x-y,x+y)","2","2")]:
            table.add(eq(tex,38).move_to([-3.9,y,0]),eq(div,38).move_to([.4,y,0]),
                      eq(curl,38).move_to([4.15,y,0]))
        if old_figure:
            others=VGroup(*(obj for index,obj in enumerate(table) if index!=6))
            entering=[FadeOut(old_figure),FadeOut(old_panel),FadeIn(others),
                      TransformMatchingShapes(old_figure[-1].copy(),table[6],fade_transform_mismatches=False)]
        else: entering=[FadeIn(table)]
        self.say("comparison",*entering,run_time=.95,transition="field-example-to-comparison-table")

    def electromagnetism(self):
        self.clear_stage(); self.header("物理例子：静电场与电势")
        center=LEFT_CENTER
        contours=VGroup(*(Ellipse(width=2*r,height=math.sqrt(2)*r,color=LINE,stroke_width=1.4)
                          .move_to(center) for r in [.7,1.15,math.sqrt(3),2.25]))
        point=Dot(center+[1,1,0],radius=.04,color=INK)
        electric=Arrow(center+[1,1,0],center+[.65,.3,0],buff=0,color=ACCENT,stroke_width=2.8)
        elabel=eq(r"\mathbf E",27,ACCENT).next_to(electric,LEFT,buff=.12)
        gfigure=VGroup(contours,point,electric,elabel,eq(r"\varphi=x^2+2y^2",28).move_to([-3.25,-2.15,0]))
        gpanel=panel(eq(r"\mathbf E=-\nabla\varphi",44),cn("静电场指向电势降低",26,MUTED))
        def potential_motion(seconds):
            def update(group,alpha):
                angle=.95+1.25*alpha
                local=np.array([math.sqrt(3)*math.cos(angle),math.sqrt(1.5)*math.sin(angle),0.])
                p=center+local; vector=-.19*np.array([2*local[0],4*local[1],0.])
                point.move_to(p); electric.put_start_and_end_on(p,p+vector)
                elabel.next_to(electric,LEFT,buff=.12)
            return [UpdateFromAlphaFunc(gfigure,update)]
        self.say("em_gradient",FadeIn(gfigure),FadeIn(gpanel),motion=potential_motion,
                 motion_kind="electric-field-normal-to-equipotentials",transition="mathematical-gradient-to-electric-potential")

        self.clear_stage(keep=(gfigure,gpanel)); self.header(r"物理例子：$\mathbf D$ 的散度与自由电荷")
        radius=.72
        def displacement(x,y):
            r=math.hypot(x,y)
            factor=3 if r<=radius else 3*radius**3/max(r,1e-6)**3
            return (factor*x,factor*y)
        darrows=field(displacement,extent=(1.4,1.4),radial_limit=1.7)
        charge=Circle(radius=radius,color=ACCENT,stroke_width=1.7,fill_color=ACCENT,fill_opacity=.08).move_to(center)
        rho=eq(r"\rho_f>0",25,ACCENT).move_to(center)
        gaussian=Circle(radius=1.12,color=INK,stroke_width=1.5).move_to(center)
        dfigure=VGroup(darrows,charge,rho,gaussian,cn("球形带电区域与高斯面截面",19,MUTED).move_to([-3.25,-2.15,0]))
        dpanel=panel(eq(r"\nabla\cdot\mathbf D=\rho_f",43),
                     eq(r"\oiint_S\mathbf D\cdot\hat{\mathbf n}\,\mathrm dS=Q_f",34),
                     cn(r"$S$：闭合高斯面；$Q_f$：包围的自由电荷",21,MUTED),
                     cn(r"$\mathbf D$：电位移矢量",25,MUTED),gap=.36)
        def gauss_motion(seconds):
            def update(group,alpha):
                r=1.05+.35*math.sin(TAU*alpha)
                gaussian.become(Circle(radius=r,color=INK,stroke_width=1.5).move_to(center))
                for arrow,seed in zip(darrows,darrows.flow_seeds):
                    scale=.88+.16*math.sin(TAU*alpha+math.atan2(seed[1],seed[0]))
                    local=seed*scale; value=np.array([*displacement(local[0],local[1]),0.])
                    value*=min(.24,.49/max(np.linalg.norm(value),1e-8))
                    arrow.put_start_and_end_on(center+local,center+local+value)
            return [UpdateFromAlphaFunc(dfigure,update)]
        self.say("em_displacement",FadeTransform(gfigure,dfigure),
                 *panel_change(gpanel,dpanel),run_time=.9,motion=gauss_motion,
                 motion_kind="gaussian-surface-and-displacement-field",transition="equipotentials-to-displacement-flux")

        self.clear_stage(keep=(dfigure,dpanel)); self.header(r"物理例子：稳恒导线周围的 $\mathbf H$")
        wire_radius=.32
        hfield=field(lambda x,y:(-y/max(x*x+y*y,wire_radius**2),x/max(x*x+y*y,wire_radius**2)),
                     extent=(1.4,1.4),radial_limit=1.7)
        wire=VGroup(Circle(radius=wire_radius,color=INK,stroke_width=1.5),Dot(radius=.05,color=INK)).move_to(center)
        ampere=Circle(radius=1.08,color=ACCENT,stroke_width=1.5).move_to(center)
        hmark=Arrow(center+[1.08,0,0],center+[1.08,.45,0],buff=0,color=ACCENT,stroke_width=2.2)
        hlabel=eq(r"\mathbf H",25,ACCENT).next_to(hmark,RIGHT,buff=.12)
        hfigure=VGroup(hfield,wire,ampere,hmark,hlabel,cn(r"电流沿屏幕外；$\mathbf H$ 沿圆周分布",19,MUTED).move_to([-3.25,-2.15,0]))
        hpanel=panel(eq(r"\nabla\times\mathbf H=\mathbf J_f",41),
                     eq(r"\frac{\partial\mathbf D}{\partial t}=\mathbf0",30,MUTED),
                     cn(r"稳恒；导线外局部旋度为 $0$",23,MUTED))
        def wire_motion(seconds):
            def update(group,alpha):
                angle=TAU*alpha
                local=1.08*np.array([math.cos(angle),math.sin(angle),0.])
                vector=.44*np.array([-math.sin(angle),math.cos(angle),0.])
                hmark.put_start_and_end_on(center+local,center+local+vector)
                hlabel.move_to(center+1.37*np.array([math.cos(angle),math.sin(angle),0.])+UP*.1)
            return [UpdateFromAlphaFunc(hfigure,update)]
        self.say("em_current",ReplacementTransform(darrows,hfield,path_arc=PI/10),
                 FadeTransform(VGroup(*dfigure[1:]),VGroup(*hfigure[1:])),*panel_change(dpanel,hpanel),
                 run_time=.9,motion=wire_motion,motion_kind="magnetic-circulation-around-steady-wire",
                 transition="electric-source-to-magnetic-circulation")

        self.clear_stage(keep=(hfigure,hpanel)); self.header("物理例子：充电电容与位移电流")
        upper=Polygon(*[center+[x,y,0] for x,y in [(-1.5,.75),(1.15,.75),(1.5,1.15),(-1.15,1.15)]],
                      color=INK,stroke_width=1.7)
        lower=upper.copy().shift(DOWN*1.9)
        leads=VGroup(Line(center+[0,1.15,0],center+[0,1.8,0],color=MUTED),
                     Line(center+[0,-1.15,0],center+[0,-1.8,0],color=MUTED))
        signs=VGroup(eq(r"+",25).move_to(center+[-1.75,.95,0]),eq(r"-",25).move_to(center+[-1.75,-.95,0]))
        dgap=VGroup(*(Arrow(center+[x,.65,0],center+[x,.1,0],buff=0,color=ACCENT,stroke_width=1.8)
                      for x in [-1.05,-.525,0,.525,1.05]))
        dlabel=eq(r"\mathbf D(t)",25,ACCENT).move_to(center+[1.15,1.5,0])
        hring=Ellipse(width=3.3,height=.54,color=LINE,stroke_width=1.6).move_to(center)
        hcap=Arrow(center+[1.65,0,0],center+[1.65,-.35,0],buff=0,color=INK,stroke_width=2.1)
        hcap_label=eq(r"\mathbf H",25).next_to(hcap,RIGHT,buff=.1)
        cfigure=VGroup(upper,lower,leads,signs,dgap,dlabel,hring,hcap,hcap_label,
                      cn("充电过程示意；忽略边缘效应",19,MUTED).move_to([-3.25,-2.15,0]))
        gap_note=cn(r"极板间：$\mathbf J_f=0$，$\mathbf D$ 随时间增大",23,MUTED)
        cpanel=panel(eq(r"\nabla\times\mathbf H=\mathbf J_f+\frac{\partial\mathbf D}{\partial t}",37),
                     eq(r"\mathbf J_d=\frac{\partial\mathbf D}{\partial t}",36),
                     gap_note)
        def capacitor_motion(seconds):
            def update(group,alpha):
                for arrow,x in zip(dgap,[-1.05,-.525,0,.525,1.05]):
                    arrow.put_start_and_end_on(center+[x,.65,0],center+[x,.65-(.5+.9*alpha),0])
                angle=TAU*1.5*alpha
                local=np.array([1.65*math.cos(angle),-.27*math.sin(angle),0.])
                vector=np.array([-1.65*math.sin(angle),-.27*math.cos(angle),0.])
                vector*=.4/max(np.linalg.norm(vector),1e-8)
                hcap.put_start_and_end_on(center+local,center+local+vector)
                hcap_label.move_to(center+local+UP*.2+RIGHT*.18)
            return [UpdateFromAlphaFunc(cfigure,update)]
        self.say("em_capacitor",ReplacementTransform(ampere,hring),
                 FadeOut(VGroup(hfield,wire,hmark,hlabel,hfigure[-1])),
                 FadeIn(VGroup(upper,lower,leads,signs,dgap,dlabel,hcap,hcap_label,cfigure[-1])),
                 *panel_change(hpanel,cpanel),
                 run_time=1,motion=capacitor_motion,motion_kind="changing-D-and-displacement-current-H",
                 transition="conduction-current-to-charging-capacitor")

        self.clear_stage(keep=(cfigure,cpanel)); self.header("从时变场到电磁波")
        wfigure,wave_moving,update_wave=transverse_wave_figure()
        wpanel=panel(eq(r"\nabla\times\mathbf H=\frac{\partial\mathbf D}{\partial t}",36),
                     eq(r"\nabla\times\mathbf E=-\frac{\partial\mathbf B}{\partial t}",36),
                     eq(r"\mathbf D=\varepsilon\mathbf E,\quad\mathbf B=\mu\mathbf H",26,MUTED),
                     eq(r"\mathbf E\perp\mathbf H,\quad\mathbf E,\mathbf H\perp\hat{\mathbf x}",29),
                     cn(r"同相；$\mathbf E\times\mathbf H$ 指向 $+x$",23,MUTED),gap=.32)
        def wave_motion(seconds):
            def update(group,alpha):
                phase=TAU*1.2*alpha
                update_wave(phase)
            return [UpdateFromAlphaFunc(wave_moving,update)]
        self.say("em_wave",FadeTransform(cfigure,wfigure),*panel_change(cpanel,wpanel),run_time=.9,
                 motion=wave_motion,motion_kind="orthogonal-transverse-electric-and-magnetic-wave",
                 transition="charging-capacitor-to-coupled-electromagnetic-wave")
        self.em_equations=wpanel

    def recap(self):
        equations=getattr(self,"em_equations",None)
        self.clear_stage(keep=(equations,) if equations is not None else ())
        self.header("三种运算的几何意义")
        rows=VGroup()
        for y,title,tex,meaning in [(1.6,"梯度",r"\nabla f","最快增加的方向与变化率"),
                                     (.15,"散度",r"\nabla\cdot\mathbf F","单位体积的局部净向外通量"),
                                     (-1.3,"旋度",r"\nabla\times\mathbf F","单位面积的局部环量，沿法向")]:
            rows.add(cn(title,28).move_to([-5,y,0]),eq(tex,40).move_to([-2.2,y,0]),
                     cn(meaning,27,width=6.9).move_to([2.6,y,0]))
        if equations:
            entering=[FadeIn(VGroup(*(obj for index,obj in enumerate(rows) if index not in [1,4,7]))),
                      TransformMatchingShapes(equations,VGroup(rows[1],rows[4],rows[7]))]
        else: entering=[FadeIn(rows)]
        self.say("summary",*entering,run_time=1.0,
                 transition="electromagnetic-equations-to-three-local-operators")

    def references(self):
        self.clear_stage(); self.header("参考资料")
        # Numbered monograph citations with hanging indentation.
        sources=VGroup()
        entries=[("[1]",2.05,[
            "徐立勤, 曹伟. 电磁场与电磁波理论[M]. 3版.",
            "北京: 科学出版社, 2018."]),
            ("[2]",.45,[
            "ULABY F T, RAVAIOLI U.",
            "Fundamentals of Applied Electromagnetics[M].",
            "8th ed. Hoboken, NJ: Pearson, 2020."]),
            ("[3]",-1.65,[
            "赵洪牛, 万彩云, 胡国雷, 等. 高等数学: 下册[M]. 2版.",
            "北京: 高等教育出版社, 2019."])]
        for number,y,lines in entries:
            body=VGroup(*(cn(line,24,width=11.6) for line in lines)).arrange(DOWN,aligned_edge=LEFT,buff=.18)
            body.shift(np.array([-5.65,y,0])-body[0].get_left())
            label=cn(number,24).move_to([-6.2,y,0])
            sources.add(label,body)
        self.say("references",FadeIn(sources),run_time=.65,
                 transition="summary-to-final-references",display_subtitle=False)


class Cover(Scene):
    def construct(self):
        self.camera.background_color=BG
        self.add(title_card())
