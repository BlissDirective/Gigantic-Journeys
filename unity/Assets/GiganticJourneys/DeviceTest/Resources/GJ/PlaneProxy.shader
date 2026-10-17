// Bedroom cleanup stage 3 (M1-PIPE-02): textured planar proxy (floor / wall quad) drawn in
// the opaque queue behind the splats. The splat composite runs with ZTest Always after the
// opaque pass, so splats always land on top and the plane only shows through holes and thin
// coverage. Unlit, gamma-space texture straight through (this project is Gamma), alpha-cut
// where no capture frame saw the texel (alpha 0 = leave it to the splats).
Shader "GJ/PlaneProxy"
{
    Properties
    {
        _MainTex ("Texture", 2D) = "white" {}
        _Color ("Tint / fallback colour", Color) = (1, 1, 1, 1)
        _Cutoff ("Alpha cutoff", Range(0, 1)) = 0.5
    }
    SubShader
    {
        Tags { "RenderType" = "TransparentCutout" "Queue" = "AlphaTest" "RenderPipeline" = "UniversalPipeline" }
        Pass
        {
            Name "PlaneProxy"
            Tags { "LightMode" = "UniversalForward" }
            ZWrite On
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_MainTex);
            SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                half4 _Color;
                half _Cutoff;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };

            Varyings Vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = TRANSFORM_TEX(v.uv, _MainTex);
                return o;
            }

            half4 Frag(Varyings i) : SV_Target
            {
                half4 c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv) * _Color;
                clip(c.a - _Cutoff);
                return half4(c.rgb, 1);
            }
            ENDHLSL
        }
    }
}
