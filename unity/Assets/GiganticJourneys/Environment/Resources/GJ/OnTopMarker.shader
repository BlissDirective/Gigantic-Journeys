// The shared non-photo marker treatment (DESIGN_SYSTEM §1, M1-GAME-01): thin light, low
// saturation, no solid geometry, always drawn on top, with depth-fade so orientation is never
// lost. Additive, ZTest Always; the part hidden behind real geometry drops to _OccludedAlpha
// when the camera depth texture is available (URP "Depth Texture" on), else draws at full.
// Shapes are procedural in UV (no textures): 0 beam, 1 sparkle, 2 footprint.
// Billboard: 0 none (footprints lie on the ground), 1 about +y (beam), 2 full (sparkle).
Shader "GJ/OnTopMarker"
{
    Properties
    {
        _Color ("Color", Color) = (1, 0.78, 0.42, 0.6)
        _OccludedAlpha ("Alpha behind geometry", Range(0, 1)) = 0.35
        _FadeStart ("Distance fade start (A)", Float) = 400
        _FadeEnd ("Distance fade end (A)", Float) = 900
        [Enum(Beam,0,Sparkle,1,Footprint,2)] _Shape ("Shape", Float) = 0
        [Enum(None,0,AxisY,1,Full,2)] _Billboard ("Billboard", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent+100" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            Name "OnTopMarker"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha One
            ZWrite Off
            ZTest Always
            Cull Off

            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _OccludedAlpha;
                float _FadeStart;
                float _FadeEnd;
                float _Shape;
                float _Billboard;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                float4 screenPos : TEXCOORD1;
                float viewDepth : TEXCOORD2;
            };

            Varyings Vert(Attributes v)
            {
                Varyings o;
                float3 centerWS = TransformObjectToWorld(float3(0, 0, 0));
                float3 positionWS;
                if (_Billboard > 1.5)
                {
                    // full billboard: quad in the camera plane, scaled by the object's x/y scale
                    float3 right = UNITY_MATRIX_V[0].xyz;
                    float3 up = UNITY_MATRIX_V[1].xyz;
                    float sx = length(GetObjectToWorldMatrix()._m00_m10_m20);
                    float sy = length(GetObjectToWorldMatrix()._m01_m11_m21);
                    positionWS = centerWS + right * v.positionOS.x * sx + up * v.positionOS.y * sy;
                }
                else if (_Billboard > 0.5)
                {
                    // about +y: the quad turns to face the camera, its height stays vertical
                    float3 toCam = GetCameraPositionWS() - centerWS;
                    float3 right = normalize(cross(float3(0, 1, 0), float3(toCam.x, 0, toCam.z) + 1e-5));
                    float sx = length(GetObjectToWorldMatrix()._m00_m10_m20);
                    float sy = length(GetObjectToWorldMatrix()._m01_m11_m21);
                    positionWS = centerWS + right * v.positionOS.x * sx + float3(0, 1, 0) * v.positionOS.y * sy;
                }
                else
                {
                    positionWS = TransformObjectToWorld(v.positionOS.xyz);
                }
                o.positionCS = TransformWorldToHClip(positionWS);
                o.screenPos = ComputeScreenPos(o.positionCS);
                o.viewDepth = -TransformWorldToView(positionWS).z;
                o.uv = v.uv;
                return o;
            }

            half ShapeAlpha(float2 uv)
            {
                float2 c = uv - 0.5;
                if (_Shape < 0.5)
                {
                    // beam: thin soft core across u, fading out towards the top
                    float core = exp(-pow(abs(c.x) * 9.0, 2.0));
                    return core * saturate(1.0 - uv.y * 0.85);
                }
                if (_Shape < 1.5)
                {
                    // sparkle: soft dot plus a four-point star
                    float r = length(c);
                    float glow = exp(-r * r * 90.0);
                    float star = exp(-abs(c.x) * 60.0) * exp(-abs(c.y) * 6.0) + exp(-abs(c.y) * 60.0) * exp(-abs(c.x) * 6.0);
                    return saturate(glow + star * 0.6);
                }
                // footprint: a soft sole ellipse
                float2 e = c * float2(2.6, 1.4);
                return saturate(1.0 - dot(e, e) * 1.8) * 0.8;
            }

            half4 Frag(Varyings i) : SV_Target
            {
                half a = _Color.a * ShapeAlpha(i.uv);
                a *= 1.0 - saturate((i.viewDepth - _FadeStart) / max(_FadeEnd - _FadeStart, 1e-3));
                float2 suv = i.screenPos.xy / i.screenPos.w;
                float raw = SampleSceneDepth(suv);
                // With the URP depth texture off the default (far plane on reversed-Z: Metal, Vulkan, D3D) never reads as occluded.
                float sceneDepth = LinearEyeDepth(raw, _ZBufferParams);
                if (i.viewDepth > sceneDepth + 0.05)
                    a *= _OccludedAlpha;
                return half4(_Color.rgb, a);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
