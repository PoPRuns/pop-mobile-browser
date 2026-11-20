#!/usr/bin/env python3
"""PoP Mobile original compact FM-style General MIDI SoundFont generator.

Copyright (C) 2026 PoP Mobile contributors.
SPDX-License-Identifier: GPL-3.0-or-later

All PCM samples are mathematically generated here. There are no external
recordings, waveform tables, commercial synth samples, or MIDI compositions.
This is a small *synthesized compatibility bank*, not a realistic GM soundbank.

Generate: python3 tools/generate_fm_soundfont.py output.sf2
"""
from __future__ import annotations

import array
import math
import random
import struct
import sys
from pathlib import Path

RATE = 22050
PERIOD = 7350  # 87 cycles; F0=261Hz, approximately middle C
TAU = math.tau


def chunk(name: bytes, data: bytes) -> bytes:
    assert len(name) == 4
    return name + struct.pack('<I', len(data)) + data + (b'\0' if len(data) % 2 else b'')


def list_chunk(name: bytes, content: bytes) -> bytes:
    return chunk(b'LIST', name + content)


def info_str(name: bytes, value: str) -> bytes:
    content = value.encode('ascii') + b'\0'
    if len(content) % 2:
        content += b'\0'
    return chunk(name, content)


def fixed_name(label: str, n: int = 20) -> bytes:
    raw = label.encode('ascii')[:n-1]
    return raw + b'\0' * (n - len(raw))


def wave(program: int) -> array.array:
    # Deterministic, family-dependent FM carrier/modulator recipes.
    family = program // 8
    variation = program % 8
    # Integer FM ratios preserve continuity at the sample loop boundary.
    carrier = 1 + (family % 3)
    mod1 = (family % 5) + 1
    mod2 = 2 + ((family + variation) % 7)
    depth = 0.2 + 0.22 * (variation % 5)
    bright = 0.05 + 0.12 * ((family + variation) % 4)
    harmonic = 2 + (variation % 4)
    amp = 0.64
    data = array.array('h')
    for i in range(PERIOD):
        phase = TAU * 87 * (i / PERIOD)
        # Four-operator-style FM with one added harmonic component.
        value = math.sin(carrier*phase + depth * math.sin(mod1*phase + 0.15*math.sin(mod2*phase)))
        value += bright * math.sin(harmonic*phase + 0.14*math.sin(phase))
        value *= (0.85 + 0.15 * math.sin(phase*2))
        data.append(max(-32768, min(32767, round(value * amp/(1+bright) * 32767))))
    return data


def drum(note: int) -> array.array:
    # Original synthesized drum hit with distinct tone/noise profiles.
    rng = random.Random(0x504F5000 + note)
    length = int(RATE * (0.14 if note in (42, 44) else (0.30 if note in (49,51,52,53,55,57,59) else 0.22)))
    out = array.array('h')
    kick = note in (35, 36)
    hat = note in (42, 44, 46, 49, 51, 52, 53, 55, 57, 59)
    snare = note in (38, 39, 40)
    frequency = (60 if kick else (190 if snare else 90 + note*2))
    for i in range(length):
        t = i / RATE
        env = math.exp(-t * (13 if kick else (29 if hat else 18)))
        noise = 2*rng.random()-1
        if kick:
            v = math.sin(TAU*(frequency*t + 20*t*math.exp(-t*30))) * env
        elif hat:
            v = (0.83*noise+0.17*math.sin(TAU*2700*t)) * env
        elif snare:
            v = (0.72*noise+0.28*math.sin(TAU*frequency*t)) * env
        else:
            v = (0.4*noise+0.6*math.sin(TAU*(frequency*t + 5*t*math.exp(-t*10)))) * env
        out.append(round(v * 19000))
    return out


def bytes_le(samples: array.array) -> bytes:
    if sys.byteorder != 'little':
        samples = samples[:]
        samples.byteswap()
    return samples.tobytes()


def generate(output: Path) -> None:
    smpl = array.array('h')
    sample_headers: list[bytes] = []
    sample_index: dict[tuple[str, int], int] = {}

    for kind, ids in [('mel', range(128)), ('drum', range(35, 82))]:
        for ident in ids:
            samples = wave(ident) if kind == 'mel' else drum(ident)
            start = len(smpl)
            smpl.extend(samples)
            end = len(smpl)
            loop_start = start + 0 if kind == 'mel' else max(start, end-48)
            loop_end = end if kind == 'mel' else end
            smpl.extend([0] * 46)  # SF2 sample interpolation guards
            sample_index[(kind, ident)] = len(sample_headers)
            sample_headers.append(struct.pack(
                '<20sIIIIIBbHH', fixed_name(f'{kind}{ident:03d}'), start, end,
                loop_start, loop_end, RATE, 60 if kind == 'mel' else ident, 0,
                0, 1  # mono sample
            ))

    # A preset points to an instrument; each instrument points to samples.
    phdr: list[bytes] = []
    pbag: list[bytes] = []
    pgen: list[bytes] = []
    inst: list[bytes] = []
    ibag: list[bytes] = []
    igen: list[bytes] = []

    def gen(op: int, amount: int) -> bytes:
        return struct.pack('<HH', op, amount & 0xFFFF)

    def inst_zone(entries: list[tuple[int, int]]) -> None:
        ibag.append(struct.pack('<HH', len(igen), 0))
        igen.extend(gen(op, amt) for op, amt in entries)

    for program in range(128):
        name = f'PM FM {program:03d}'
        phdr.append(struct.pack('<20sHHHIII', fixed_name(name), program, 0, len(pbag), 0, 0, 0))
        pbag.append(struct.pack('<HH', len(pgen), 0))
        pgen.append(gen(41, len(inst)))  # instrument
        inst.append(struct.pack('<20sH', fixed_name(name), len(ibag)))
        release = -1900 if program//8 in (0, 1, 2) else -3000
        inst_zone([(34, -8200),  # attackVolEnv: ~8.8ms
                   (38, release), # releaseVolEnv
                   (48, 80),     # initialAttenuation: 8dB
                   (54, 1),      # sampleModes: continuous loop
                   (53, sample_index[('mel', program)])])

    phdr.append(struct.pack('<20sHHHIII', fixed_name('PM FM DRUMS'), 0, 128, len(pbag), 0, 0, 0))
    pbag.append(struct.pack('<HH', len(pgen), 0))
    pgen.append(gen(41, len(inst)))
    inst.append(struct.pack('<20sH', fixed_name('PM FM DRUMS'), len(ibag)))
    for note in range(35, 82):
        inst_zone([(43, note | (note << 8)),  # keyRange [note,note]
                   (53, sample_index[('drum', note)])])

    phdr.append(struct.pack('<20sHHHIII', fixed_name('EOP'), 0, 0, len(pbag), 0, 0, 0))
    pbag.append(struct.pack('<HH', len(pgen), 0))
    pgen.append(gen(60, 0))
    inst.append(struct.pack('<20sH', fixed_name('EOI'), len(ibag)))
    ibag.append(struct.pack('<HH', len(igen), 0))
    igen.append(gen(60, 0))
    sample_headers.append(struct.pack('<20sIIIIIBbHH', fixed_name('EOS'), len(smpl),
                                      len(smpl), len(smpl), len(smpl), RATE, 0, 0, 0, 1))

    info = list_chunk(b'INFO', b''.join([
        chunk(b'ifil', struct.pack('<HH', 2, 1)),
        info_str(b'isng', 'EMU8000'),
        info_str(b'INAM', 'PoP Mobile Original FM GM'),
        info_str(b'ICRD', '2026-11-20'),
        info_str(b'IENG', 'PoP Mobile contributors'),
        info_str(b'ICOP', '2026 PoP Mobile contributors; GPL-3.0-or-later'),
        info_str(b'ICMT', 'All sounds generated algorithmically; see generate_fm_soundfont.py'),
    ]))
    sdta = list_chunk(b'sdta', chunk(b'smpl', bytes_le(smpl)))
    pdta = list_chunk(b'pdta', b''.join([
        chunk(b'phdr', b''.join(phdr)),
        chunk(b'pbag', b''.join(pbag)),
        chunk(b'pmod', bytes(10)),
        chunk(b'pgen', b''.join(pgen)),
        chunk(b'inst', b''.join(inst)),
        chunk(b'ibag', b''.join(ibag)),
        chunk(b'imod', bytes(10)),
        chunk(b'igen', b''.join(igen)),
        chunk(b'shdr', b''.join(sample_headers)),
    ]))
    content = b'sfbk' + info + sdta + pdta
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(chunk(b'RIFF', content))
    print(f'Wrote {output}: {output.stat().st_size:,} bytes / 128 melodic programs + 47 drum keys')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 generate_fm_soundfont.py output.sf2')
    generate(Path(sys.argv[1]))
