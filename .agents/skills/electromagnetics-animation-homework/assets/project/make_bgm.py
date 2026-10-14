"""Compose a quiet original instrumental track and mux it without re-encoding video.

No external music, samples, vocals, or downloads. NumPy synthesis, PyAV AAC mux.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import wave

import av
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly

ROOT=Path(__file__).resolve().parent
RATE=48000
BPM=78


def pitch(note):
    return 440*2**((note-69)/12)


def piano(note,seconds,velocity=1.):
    t=np.arange(round(seconds*RATE))/RATE
    f=pitch(note)
    tone=np.sin(2*np.pi*f*t+.48*np.exp(-t/.45)*np.sin(4*np.pi*f*t))
    tone+=.08*np.sin(6*np.pi*f*t)*np.exp(-t/.7)
    envelope=(1-np.exp(-t/.014))*np.exp(-t/1.65)
    envelope*=np.minimum(1,np.maximum(0,seconds-t)/.35)
    return velocity*tone*envelope


def pad(note,hold):
    seconds=hold+2.
    t=np.arange(round(seconds*RATE))/RATE
    f=pitch(note)
    tone=(np.sin(2*np.pi*f*2**(-3/1200)*t)+np.sin(2*np.pi*f*2**(3/1200)*t))*.5
    tone+=.12*np.sin(4*np.pi*f*t)
    envelope=(1-np.exp(-t/.65))*np.exp(-np.maximum(0,t-hold)/.55)
    return tone*envelope


def write_wav(path,samples,rate=RATE):
    pcm=np.round(np.clip(samples,-1,1)*32767).astype('<i2')
    with wave.open(str(path),'wb') as output:
        output.setnchannels(2);output.setsampwidth(2);output.setframerate(rate)
        output.writeframes(pcm.tobytes())


def compose(seconds):
    count=round(seconds*RATE)
    mix=np.zeros((count,2),dtype=np.float64)
    beat=60/BPM;hold=8*beat
    chords=[(50,54,57,61,64),(45,52,57,59,61),(47,54,57,62,66),(43,50,54,57,59)]
    bass=[38,33,35,31]
    melodies=[[(.5,66),(2.5,69),(4.5,64),(6.5,62)],
              [(1,64),(3,61),(5.5,59)],[(.5,62),(3,66),(5.5,69)],
              [(1,67),(3.5,66),(5,64),(7,62)]]
    def add(t,signal,gain,pan=0.):
        start=round(t*RATE)
        if start>=count:return
        signal=signal[:count-start]*gain
        angle=(pan+1)*np.pi/4
        mix[start:start+len(signal),0]+=signal*np.cos(angle)
        mix[start:start+len(signal),1]+=signal*np.sin(angle)
    for bar,start in enumerate(np.arange(0,max(0,seconds-7),hold)):
        index=bar%4;chord=chords[index]
        for j,note in enumerate(chord):
            add(start,pad(note,hold),.085,pan=(j-2)*.17)
        for offset in [0,4]:
            add(start+offset*beat,piano(bass[index],2.4),.14)
        for j,offset in enumerate([0,2,4,6]):
            add(start+offset*beat,piano(chord[1+j%3],3.1),.16,pan=(-1)**j*.18)
        for j,(offset,note) in enumerate(melodies[index]):
            if start+offset*beat<seconds-7:
                add(start+offset*beat,piano(note,3.8),.32,pan=(-1)**(bar+j)*.24)
    # A restrained tonic resolution before the final fade.
    ending=max(0,seconds-6)
    for j,note in enumerate(chords[0]):add(ending,pad(note,4),.055,pan=(j-2)*.16)
    add(ending,piano(62,4.8),.22)
    dry=mix.copy()
    for delay,gain in [(.13,.10),(.27,.07),(.43,.055),(.67,.035),(.91,.025)]:
        shift=round(delay*RATE)
        mix[shift:,0]+=gain*dry[:-shift,1]
        mix[shift:,1]+=gain*dry[:-shift,0]
    mix=sosfilt(butter(2,[35,4200],btype='bandpass',fs=RATE,output='sos'),mix,axis=0)
    t=np.arange(count)/RATE
    fade=np.minimum(1,t/2.)**2*np.minimum(1,np.maximum(0,seconds-t)/3.5)**2
    mix*=fade[:,None]
    rms=float(np.sqrt(np.mean(mix**2)))
    gain=min(10**(-28/20)/max(rms,1e-10),.18/max(np.max(np.abs(mix)),1e-10))
    return (mix*gain).astype(np.float32)


def mux(video_path,destination,music):
    with av.open(str(video_path)) as source,av.open(str(destination),'w',options={'movflags':'+faststart'}) as output:
        video=source.streams.video[0]
        copied=output.add_stream_from_template(video)
        audio=output.add_stream('aac',rate=RATE)
        audio.layout='stereo';audio.bit_rate=160000
        for packet in source.demux(video):
            if packet.dts is not None:
                packet.stream=copied;output.mux(packet)
        for offset in range(0,len(music),1024):
            data=np.ascontiguousarray(music[offset:offset+1024].T)
            frame=av.AudioFrame.from_ndarray(data,format='fltp',layout='stereo')
            frame.sample_rate=RATE;frame.pts=offset;frame.time_base=Fraction(1,RATE)
            for packet in audio.encode(frame):output.mux(packet)
        for packet in audio.encode(None):output.mux(packet)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    with av.open(args.video) as source:
        stream=source.streams.video[0]
        duration=float(stream.duration*stream.time_base)
    folder=ROOT/'output';folder.mkdir(exist_ok=True)
    music=compose(duration)
    write_wav(folder/'bgm_original.wav',music)
    write_wav(folder/'bgm_preview.wav',music[12*RATE:32*RATE])
    # Small low-bandwidth audition copy, separate from the full-quality master.
    audition=resample_poly(np.mean(music[12*RATE:20*RATE],axis=1),1,6)
    with wave.open(str(folder/'bgm_audition.wav'),'wb') as sample:
        sample.setnchannels(1);sample.setsampwidth(2);sample.setframerate(8000)
        sample.writeframes(np.round(np.clip(audition,-1,1)*32767).astype('<i2').tobytes())
    rms=float(np.sqrt(np.mean(music.astype(float)**2)));peak=float(np.max(np.abs(music)))
    manifest={'kind':'original_background_music','title':'场的微光','narration':False,
              'composition':'procedural original composition, no external samples',
              'instruments':['warm electric piano','soft synth pad','muted bass'],
              'bpm':BPM,'sample_rate':RATE,'channels':2,'seconds':len(music)/RATE,
              'rms_dbfs':float(20*np.log10(rms)),'peak_dbfs':float(20*np.log10(peak)),
              'fade_in_seconds':2.,'fade_out_seconds':3.5,'video_reencoded':False}
    (folder/'bgm_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),'utf-8')
    mux(Path(args.video),Path(args.output),music)
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
