"""Artifact QA: storyboard snapshots, stream checks, decoded frames and contact sheets."""
import argparse
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parent


def contact_sheet(paths, destination, columns=3):
    thumb_w,thumb_h=640,360
    rows=(len(paths)+columns-1)//columns
    canvas=Image.new("RGB",(columns*thumb_w,rows*(thumb_h+28)),"#000000")
    draw=ImageDraw.Draw(canvas)
    for index,path in enumerate(paths):
        img=Image.open(path).convert("RGB")
        img.thumbnail((thumb_w,thumb_h))
        x=(index%columns)*thumb_w; y=(index//columns)*(thumb_h+28)
        canvas.paste(img,(x,y))
        draw.text((x+12,y+thumb_h+5),path.stem,fill="white")
    canvas.save(destination)


def stills():
    from manim import tempconfig
    from vector_calculus import VectorCalculus
    output=ROOT/"qa"/"storyboard_subtitle_animation"
    output.mkdir(parents=True,exist_ok=True)
    original=VectorCalculus.say
    warnings=[]
    paths=[]
    def snapshot(scene,key,*animations,**kwargs):
        original(scene,key,*animations,**kwargs)
        scene.renderer.update_frame(scene,ignore_skipping=True)
        destination=output/f"{len(scene.timeline):02d}_{key}.png"
        scene.renderer.camera.get_image().save(destination)
        paths.append(destination)
        # Only flag objects outside the outer frame. Subtitle area is intentional.
        for obj in scene.mobjects:
            if obj.width and (obj.get_left()[0]<-7.12 or obj.get_right()[0]>7.12
                              or obj.get_top()[1]>4.01 or obj.get_bottom()[1]<-4.01):
                warnings.append({"segment":key,"object":type(obj).__name__,
                                 "bounds":[obj.get_left()[0],obj.get_right()[0],obj.get_bottom()[1],obj.get_top()[1]]})
    VectorCalculus.say=snapshot
    # Storyboard QA must not overwrite the final video's frame-accurate timeline.
    def storyboard_timeline(scene,name):
        (ROOT/"qa"/"storyboard_timeline.json").write_text(
            json.dumps(scene.timeline,ensure_ascii=False,indent=2),"utf-8")
    VectorCalculus.write_timeline=storyboard_timeline
    with tempconfig({"dry_run":True,"skip_animations":True,"pixel_width":1280,
                     "pixel_height":720,"progress_bar":"none","verbosity":"ERROR"}):
        VectorCalculus().render()
    for start in range(0,len(paths),12):
        contact_sheet(paths[start:start+12],ROOT/"qa"/f"subtitle_storyboard_{start//12+1}.jpg")
    (ROOT/"qa"/"layout_subtitle.json").write_text(json.dumps(warnings,indent=2),"utf-8")
    print(f"Storyboard: {len(paths)} frames; frame-boundary warnings: {len(warnings)}")


def verify_gradient_tracking(path):
    samples=json.loads((ROOT/"qa"/"gradient_track_full.json").read_text("utf-8"))
    assert len(samples)>300,"Missing per-frame gradient tracking data"
    anchor_errors=[]; normal_errors=[]; label_errors=[]
    for sample in samples:
        x,y,z=sample["world_point"]
        assert abs(z-x*x-2*y*y)<1e-9,"Point has left the paraboloid"
        tangent=np.array(sample["world_tangent"])
        normal_errors.append(abs(float(tangent@np.array([-2*x,-4*y,1]))))
        anchor_errors.append(float(np.linalg.norm(np.array(sample["point"])-sample["arrow_start"])))
        delta=(np.array(sample["label_left"])-sample["arrow_end"])[:2]
        label_errors.append(float(np.linalg.norm(delta-[.14,0])))
    assert max(anchor_errors)<1e-8,"Gradient arrow detached from the surface point"
    assert max(normal_errors)<1e-8,"Gradient lift is not tangent to the graph"
    assert max(label_errors)<1e-8,"Gradient label detached from the arrow"
    groups=[[s for s in samples if s["phase"]==phase]
            for phase in ["grad_geometry","grad_directional","grad_formula"]]
    spans=[]
    for group in groups:
        angles=np.array([s["angle"] for s in group])
        assert len(group)>90 and np.ptp(angles)>.4,"Surface point frozen during a gradient segment"
        assert np.min(np.diff(angles))>=-1e-9 and np.max(np.diff(angles))<.02,"Trajectory jumps"
        spans.append(float(np.linalg.norm(np.array(group[-1]["point"])-group[0]["point"])))
    for before,after in zip(groups,groups[1:]):
        assert np.linalg.norm(np.array(before[-1]["point"])-after[0]["point"])<1e-8,"Segment boundary jump"
    times=np.array([s["seconds"] for s in samples])
    checked=0; min_label_pixels=10**9; max_below_point=-float("inf")
    with av.open(str(path)) as container:
        video=container.streams.video[0]
        frame_width=8*video.width/video.height
        container.seek(int(times[0]/float(video.time_base)),stream=video,backward=True)
        for frame in container.decode(video):
            t=float(frame.time)
            if t<times[0]+.1:continue
            if t>times[-1]-.1:break
            index=int(np.searchsorted(times,t))
            choices=[max(0,index-1),min(len(samples)-1,index)]
            sample=samples[min(choices,key=lambda i:abs(times[i]-t))]
            a=frame.to_ndarray(format="rgb24").astype(np.int16)
            blue=(a[:,:,2]-a[:,:,0]>20)&(a[:,:,1]-a[:,:,0]>10)&(a[:,:,0]>45)
            left,bottom,right,top=sample["label_bounds"]
            x0=max(0,int((left/frame_width+.5)*video.width)-12)
            x1=min(video.width,int((right/frame_width+.5)*video.width)+12)
            y0=max(0,int((.5-top/8)*video.height)-12)
            y1=min(video.height,int((.5-bottom/8)*video.height)+12)
            count=int(np.sum(blue[y0:y1,x0:x1]));min_label_pixels=min(min_label_pixels,count)
            assert count>20,f"Rendered gradient label missing from its expected position at {t:.3f}s"
            ys,_=np.where(blue[int(.13*video.height):int(.76*video.height),
                                int(.04*video.width):int(.49*video.width)])
            assert len(ys),"Gradient arrow missing from rendered frame"
            point_y=(.5-sample["point"][1]/8)*video.height
            below=float(np.max(ys)+int(.13*video.height)-point_y)
            max_below_point=max(max_below_point,below)
            assert below<12,f"Gradient marking reappeared below the surface point at {t:.3f}s"
            checked+=1
    assert checked>300,"Insufficient decoded gradient frames"
    return {"decoded_frames_checked":checked,"max_arrow_anchor_error":max(anchor_errors),
            "max_tangent_normal_dot":max(normal_errors),"max_label_offset_error":max(label_errors),
            "minimum_label_blue_pixels":min_label_pixels,"max_blue_pixels_below_point":max_below_point,
            "surface_point_motion_spans":spans}


def verify_plane_wave_model():
    from vector_calculus import plane_wave_vectors
    positions=np.linspace(-2.2,2.2,41)
    max_dot=0.;max_longitudinal=0.;max_phase_error=0.;min_flux=0.
    for phase in np.linspace(0,2*np.pi,17):
        electric,magnetic=plane_wave_vectors(positions,phase)
        max_dot=max(max_dot,float(np.max(np.abs(np.sum(electric*magnetic,axis=-1)))))
        max_longitudinal=max(max_longitudinal,float(np.max(np.abs(electric[:,0]))),
                             float(np.max(np.abs(magnetic[:,0]))))
        expected_magnetic=np.cross([1.,0,0],electric)
        max_phase_error=max(max_phase_error,float(np.max(np.abs(magnetic-expected_magnetic))))
        min_flux=min(min_flux,float(np.min(np.cross(electric,magnetic)[:,0])))
        # Increasing phase moves a fixed feature toward +x.
        later=plane_wave_vectors(positions+.2,phase+2.3*.2)
        assert np.allclose(later[0],electric) and np.allclose(later[1],magnetic),"Wave travels in the wrong direction"
    assert max_dot<1e-10 and max_longitudinal<1e-10,"Fields are not mutually transverse"
    assert max_phase_error<1e-10 and min_flux>=-1e-10,"Field phase or Poynting direction is incorrect"
    return {"sampled_field_pairs":41*17,"max_E_dot_H":max_dot,
            "max_longitudinal_component":max_longitudinal,"max_normalized_H_minus_x_cross_E":max_phase_error,
            "minimum_poynting_x":min_flux}


def verify_bgm(path):
    manifest=json.loads((ROOT/"output"/"bgm_manifest.json").read_text("utf-8"))
    assert manifest["kind"]=="original_background_music" and manifest["narration"] is False
    with av.open(str(path)) as container:
        assert len(container.streams.audio)==1,"Expected one instrumental BGM track"
        stream=container.streams.audio[0]
        assert stream.codec_context.name=="aac" and len(stream.layout.channels)==2
        pcm=np.concatenate([frame.to_ndarray() for frame in container.decode(stream)],axis=1).astype(float)
        rate=stream.codec_context.sample_rate
        rms=float(np.sqrt(np.mean(pcm**2)));peak=float(np.max(np.abs(pcm)))
        middle=pcm[:,int(10*rate):int(100*rate)]
        body_rms=float(np.sqrt(np.mean(middle**2)))
        intro=float(np.sqrt(np.mean(pcm[:,:int(.25*rate)]**2)))
        outro=float(np.sqrt(np.mean(pcm[:,-int(.25*rate):]**2)))
        audio_seconds=float(stream.duration*stream.time_base)
    assert .01<rms<.07 and peak<.3,"BGM is silent, too loud, or clipped"
    assert intro<body_rms*.4 and outro<body_rms*.4,"Music lacks a gentle fade"
    assert abs(audio_seconds-manifest["seconds"])<.12,"Music duration mismatch"
    return {"codec":"aac","channels":2,"sample_rate":rate,"seconds":audio_seconds,
            "rms_dbfs":float(20*np.log10(rms)),"peak_dbfs":float(20*np.log10(peak)),
            "intro_quarter_second_rms":intro,"outro_quarter_second_rms":outro,
            "kind":manifest["kind"],"narration":False}


def inspect_video(path):
    path=Path(path)
    out=ROOT/"qa"/"final_frames_subtitle_animation"
    out.mkdir(parents=True,exist_ok=True)
    timeline=json.loads((ROOT/"output"/"timeline_full.json").read_text("utf-8"))
    expected=json.loads((ROOT/"narration.json").read_text("utf-8"))
    assert [s["id"] for s in timeline]==[s["id"] for s in expected],"Narration/timeline mismatch"
    assert not any(word in s["text"]+s["caption"] for s in timeline
                   for word in ["练习","暂停","答案","课后"]),"Unexpected exercise content"
    for segment,item in zip(timeline,expected,strict=True):
        assert segment["subtitle"].replace("\n","")==item["text"],"Incomplete on-screen explanation"
        assert abs(segment["end"]-segment["start"]-item["seconds"])<=.09,"Segment timing drift"
    srt=(ROOT/"output"/"lesson_full.srt").read_text("utf-8-sig")
    assert all(s["subtitle"] in srt for s in timeline),"Incomplete exported subtitles"
    paths=[]
    with av.open(str(path)) as container:
        video=container.streams.video[0]
        assert len(container.streams.audio)==1,"Expected instrumental background music"
        duration=float(container.duration/av.time_base)
        report={"file":str(path),"width":video.width,"height":video.height,
                "fps":float(video.average_rate),"seconds":duration,"video_codec":video.codec_context.name,
                "audio_streams":len(container.streams.audio),"segments":len(timeline),
                "subtitle_segments":sum(s.get("presentation","subtitle")=="subtitle" for s in timeline),
                "card_segments":sum(s.get("presentation")=="card" for s in timeline),
                "video_seconds":float(video.duration*video.time_base),
                "sample_frames":[],"motion_checks":[]}
        report["planned_seconds"]=sum(s["seconds"] for s in expected)
        report["transitions"]=sum(bool(s["transition"]) for s in timeline)
        def decode_at(target):
            container.seek(int(target/float(video.time_base)),stream=video,backward=True)
            return next(f for f in container.decode(video) if float(f.time)>=target)
        for index,segment in enumerate(timeline):
            target=segment["end"]-.25
            frame=decode_at(target)
            image=frame.to_image()
            pixels=np.array(image)
            assert np.std(pixels)>5,f"Empty frame in {segment['id']}"
            assert np.max(pixels[8:35,8:35])<=2,"Background is not pure black"
            destination=out/f"{index+1:02d}_{segment['id']}.jpg"
            image.save(destination,quality=92)
            paths.append(destination)
            report["sample_frames"].append({"segment":segment["id"],"seconds":float(frame.time)})
            if segment["motion_kind"]:
                motion_start=segment["motion_start"]
                samples=[]
                for phase in [.23,.67]:
                    sample=decode_at(motion_start+(segment["end"]-motion_start)*phase).to_image()
                    sample.save(out/f"motion_{segment['id']}_{phase:.2f}.jpg",quality=92)
                    a=np.array(sample).astype(float)
                    # Diagram region excludes the fixed title, equations, and subtitles.
                    samples.append(a[int(.16*video.height):int(.78*video.height),
                                     int(.04*video.width):int(.49*video.width)])
                difference=float(np.mean(np.abs(samples[0]-samples[1])))
                assert difference>.05,f"Static diagram: {segment['id']}"
                report["motion_checks"].append({"segment":segment["id"],"kind":segment["motion_kind"],
                                                "mean_pixel_difference":difference})
    report["final_hold_seconds"]=report["video_seconds"]-timeline[-1]["end"]
    assert 0<=report["final_hold_seconds"]<=.3,"Excessive final hold"
    assert duration>=timeline[-1]["end"]-.2,"Video is truncated"
    assert abs(duration-report["planned_seconds"])<1,"Unexpected total duration"
    report["gradient_tracking"]=verify_gradient_tracking(path)
    report["plane_wave_physics"]=verify_plane_wave_model()
    report["background_music"]=verify_bgm(path)
    for start in range(0,len(timeline),12):
        contact_sheet(paths[start:start+12],ROOT/"qa"/f"subtitle_final_{start//12+1}.jpg")
    (ROOT/"output"/"verification.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),"utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="sample_frames"},ensure_ascii=False,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--stills",action="store_true")
    parser.add_argument("--video")
    args=parser.parse_args()
    if args.stills: stills()
    if args.video: inspect_video(args.video)
