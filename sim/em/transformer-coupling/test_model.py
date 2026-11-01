"""Analytical checks for the balanced board-path network composition."""
# SPDX-License-Identifier: CERN-OHL-P-2.0
import importlib.util
import json
from pathlib import Path
import numpy as np
import skrf as rf

spec = importlib.util.spec_from_file_location('board_path_model', Path(__file__).with_name('model.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_series_resistor_matches_closed_form():
    f = np.array([1e6, 4e6, 10e6])
    n = rf.Network(f=f, a=m.series(np.full(3, 100.)), z0=100)
    np.testing.assert_allclose(n.s[:,1,0], 2/3, atol=1e-14)
    np.testing.assert_allclose(n.s[:,0,0], 1/3, atol=1e-14)


def test_shunt_capacitor_matches_closed_form():
    f = np.array([1e6, 4e6, 10e6])
    y = 2j*np.pi*f*110e-12
    n = rf.Network(f=f, a=m.shunt(y), z0=100)
    np.testing.assert_allclose(n.s[:,1,0], 2/(2+100*y), atol=1e-14)


def test_series_reduction_preserves_power_and_reciprocity():
    z = np.array([[70,10,2], [10,80,3], [2,3,100]], dtype=complex)
    original = rf.Network(f=[4e6], z=z[None,:,:], z0=50)
    c = np.array([[1,0],[1,0],[0,1]])
    reduced = m.reduce_ports(original, c)
    np.testing.assert_allclose(reduced.z[0], c.T @ z @ c, atol=1e-12)
    current = np.array([.2+.1j, -.3j])
    np.testing.assert_allclose(np.vdot(c@current,z@(c@current)),
                               np.vdot(current,reduced.z[0]@current), atol=1e-12)
    assert max(np.linalg.svd(reduced.s[0], compute_uv=False)) <= 1


def test_component_network_is_passive_and_reciprocal():
    config = json.loads(Path(__file__).with_name('model.json').read_text())
    f = np.linspace(1e6, 10e6, 10)
    load, resistors, transformer = m.component_abcd(f, config)
    network = rf.Network(f=f, a=load @ resistors @ transformer, z0=100)
    assert np.max(np.linalg.svd(network.s, compute_uv=False)) < 1
    np.testing.assert_allclose(network.s[:,0,1], network.s[:,1,0], atol=1e-12)


def test_dependent_port_connection_is_rejected():
    import pytest
    with pytest.raises(ValueError):
        m.reduce_ports(rf.Network(f=[4e6], z=np.eye(3)[None,:,:], z0=50), [[1,0],[0,0],[0,0]])


def test_route_crosses_saved_pad_bridge():
    def component(x):
        return {'pads':[{'number':'1','net':'COM','position':[x,0]}]}
    components={'A':component(0),'B':component(2),'BRIDGE':component(1.1)}
    board={'copper':[
        {'kind':'track','net':'COM','start':[0,0],'end':[1,0]},
        {'kind':'track','net':'COM','start':[1.2,0],'end':[2,0]},
        {'kind':'pad','net':'COM','polygons':[{'outer':[[.9,-.1],[1.3,-.1],[1.3,.1],[.9,.1]],'holes':[]}]}]}
    assert abs(m.route_length(board,components,'A:1','B:1')['length_mm']-2)<1e-12


def test_section_line_matches_lossless_delay(tmp_path):
    p=tmp_path/'postprocess';p.mkdir()
    l,c=1e-6,1e-10
    (p/'report.json').write_text(json.dumps({'differential_candidates':[{'L_PV[1] (H/m)':l,'C_PV[1] (F/m)':c}]}))
    f=np.array([1e6,4e6,10e6]);length=.02
    network,parameters=m.section_line(tmp_path,f,length)
    np.testing.assert_allclose(network.s[:,1,0],np.exp(-2j*np.pi*f*np.sqrt(l*c)*length),atol=1e-12)
    np.testing.assert_allclose(network.s[:,0,0],0,atol=1e-12)
    assert parameters['Z_ohms']==100
