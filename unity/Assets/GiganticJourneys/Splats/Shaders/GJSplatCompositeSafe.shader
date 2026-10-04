// Alpha-safe replacement for the pinned package's "Hidden/Gaussian Splatting/Composite"
// (ticket M1-UNITY-01). The package divides the premultiplied splat colour by its alpha.
// Where no splat survives the depth test (for example every splat behind the character),
// that is 0/0 = NaN; on Metal (half precision) the NaN blends to black, so opaque objects
// among splats turned black on the iPhone (build 48). This version skips such pixels and
// clamps the un-premultiplied colour, which also stops faint fringes blowing out to white.
// The package stays unmodified: GaussianSplatRenderer.m_ShaderComposite points here.
Shader "Hidden/GJ/Gaussian Splatting/Composite Alpha-Safe"
{
    SubShader
    {
        Pass
        {
            ZWrite Off
            ZTest Always
            Cull Off
            Blend SrcAlpha OneMinusSrcAlpha

CGPROGRAM
#pragma vertex vert
#pragma fragment frag
#pragma require compute
#pragma use_dxc
#include "UnityCG.cginc"

struct v2f
{
    float4 vertex : SV_POSITION;
};

v2f vert (uint vtxID : SV_VertexID)
{
    v2f o;
    float2 quadPos = float2(vtxID&1, (vtxID>>1)&1) * 4.0 - 1.0;
    o.vertex = float4(quadPos, 1, 1);
    return o;
}

Texture2D _GaussianSplatRT;

float4 frag (v2f i) : SV_Target
{
    float4 col = _GaussianSplatRT.Load(int3(i.vertex.xy, 0));
    // Nothing (or next to nothing) drawn here: keep the scene colour untouched.
    if (!(col.a >= 1.0 / 255.0))
        discard;
    float3 rgb = saturate(col.rgb / col.a);
    return float4(GammaToLinearSpace(rgb), saturate(col.a));
}
ENDCG
        }
    }
}
