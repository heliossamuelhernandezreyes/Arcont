# Graphics and Asset Delivery Foundations

Scope: shared, 2D, 2.5D, 3D
Status: SOURCE-EXTRACTED; not universal benchmark rules

## Vulkan synchronization

Khronos documents synchronization as an explicit responsibility of Vulkan applications. Poor synchronization can create correctness hazards and can also leave the GPU unnecessarily idle. Pipeline stages and synchronization scopes exist so dependencies can be constrained rather than globally stalling unrelated work.

ARCONT consequence: synchronization advice must be expressed as dependency/resource-access reasoning, not as blanket 'add a barrier' rules. Performance effects require runtime evidence on the relevant backend/hardware.

## KTX 2.0 and Basis Universal

KTX 2.0 is a GPU texture container designed for efficient delivery across platforms. It supports mip levels, streaming-oriented access, Basis Universal payloads and supercompression. The glTF KHR_texture_basisu extension allows KTX2/Basis textures to be delivered in glTF and transcoded at runtime to a GPU-supported block-compressed format.

ARCONT consequence: asset-pipeline experiments should compare at least transmission size, decode/transcode cost, upload time, resident GPU memory, visual quality and platform format support. PNG/JPEG file size alone is not a useful proxy for runtime texture cost.

## 2D

Study separately:
- sprite count versus submitted draw work;
- atlas/material/texture changes;
- transparent overdraw;
- tilemap chunk size and rebuild cost;
- particles;
- 2D lighting/shadows;
- texture compression and mip behavior where applicable.

## 2.5D

Treat 2.5D as a family of hybrid constraints rather than a single renderer. Record whether gameplay is planar, whether visuals are 2D or 3D, camera projection, depth usage, lighting model and physics dimension. Never transfer a 2D or 3D optimization to 2.5D without stating which layer it applies to.

## 3D

Study independently:
- visible object count;
- draw calls/submission;
- instancing;
- vertex/triangle load;
- fragment/overdraw load;
- materials/shaders;
- shadows;
- culling;
- LOD/HLOD;
- texture residency;
- streaming;
- post-processing.

## Benchmark questions generated

1. What is the cost curve of texture/material changes compared with instance count?
2. At what workload does instancing materially alter CPU submission cost on each renderer/device?
3. How does KTX2/Basis affect package size, transcode time, upload time and resident memory on Android?
4. How does transparent overdraw scale for 2D sprites and 2.5D billboard-heavy scenes?
5. Which synchronization changes alter GPU idle time without changing output on Vulkan backends?

These are hypotheses/questions, not conclusions.
