import {useEffect,useMemo,useRef,useState} from 'react';
import {Canvas,useFrame,useLoader,useThree} from '@react-three/fiber';
import {Float,OrbitControls} from '@react-three/drei';
import type {ThreeEvent} from '@react-three/fiber';
import {Box3,Color,DoubleSide,MathUtils,Mesh,MeshBasicMaterial,NormalBlending,PerspectiveCamera,Quaternion,SRGBColorSpace,TextureLoader,Vector3} from 'three';
import type {Group,Material} from 'three';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';
import {RotateCcw,Scan} from 'lucide-react';
import './astronaut-scene.css';

export type BodyRegion='head'|'chest'|'torso'|'arms'|'legs';
const labels:BodyRegion[]=['head','chest','torso','arms','legs'];
const suitModelUrl='/models/astronaut-jungle-jim.fbx';
type Zone={position:[number,number,number];scale:[number,number,number];rotation?:[number,number,number]};
const zones:Record<BodyRegion,Zone[]>={
 head:[{position:[0,1.34,.16],scale:[.39,.38,.43]}],
 chest:[{position:[0,.52,.24],scale:[.47,.5,.42]}],
 torso:[{position:[0,-.2,.22],scale:[.42,.39,.38]}],
 arms:[{position:[-.64,.24,.48],scale:[.2,.46,.17],rotation:[0,0,.58]},{position:[.64,.24,.48],scale:[.2,.46,.17],rotation:[0,0,-.58]}],
 legs:[{position:[-.23,-1.06,.22],scale:[.27,.59,.32]},{position:[.23,-1.06,.22],scale:[.27,.59,.32]}]
};
export const crewSuitColors:Record<string,string>={'CREW-01':'#9c5e0b','CREW-02':'#0b7189','CREW-03':'#6246aa','CREW-04':'#a33e5e'};
export const getCrewSuitColor=(crewMemberId:string)=>crewSuitColors[crewMemberId]??crewSuitColors['CREW-01'];

function hasColor(material:Material):material is Material & {color:Color}{
 return 'color' in material&&material.color instanceof Color;
}

function SpaceBackdrop(){
 const texture=useLoader(TextureLoader,'/images/earth-horizon-background.jpg');
 const camera=useThree(state=>state.camera);
 const renderer=useThree(state=>state.gl);
 const size=useThree(state=>state.size);
 const backdrop=useRef<Mesh|null>(null);
 const cameraPosition=useMemo(()=>new Vector3(),[]);
 const cameraDirection=useMemo(()=>new Vector3(),[]);
 const cameraQuaternion=useMemo(()=>new Quaternion(),[]);
 const distance=30;
 const fov=camera instanceof PerspectiveCamera?camera.fov:43;
 const height=2*distance*Math.tan(MathUtils.degToRad(fov)/2);
 const imageAspect=texture.image.width/texture.image.height;
 const width=height*Math.max(imageAspect,size.width/size.height);
 const planeHeight=width/imageAspect;
 texture.colorSpace=SRGBColorSpace;
 texture.anisotropy=renderer.capabilities.getMaxAnisotropy();
 useFrame(()=>{
  if(!backdrop.current)return;
  camera.getWorldPosition(cameraPosition);
  camera.getWorldDirection(cameraDirection);
  camera.getWorldQuaternion(cameraQuaternion);
  backdrop.current.position.copy(cameraPosition).addScaledVector(cameraDirection,distance);
  backdrop.current.quaternion.copy(cameraQuaternion);
 });
 return <mesh ref={backdrop}>
  <planeGeometry args={[width,planeHeight]}/>
  <meshBasicMaterial map={texture} depthWrite={false} toneMapped={false}/>
 </mesh>
}

function BodyHotspot({zone,region,onChange,onHover}:{zone:Zone;region:BodyRegion;onChange:(region:BodyRegion)=>void;onHover:(region:BodyRegion|null)=>void}){
 return <mesh name={`body-hotspot-${region}`} position={zone.position} rotation={zone.rotation} scale={zone.scale} onPointerOver={(event:ThreeEvent<PointerEvent>)=>{event.stopPropagation();onHover(region)}} onPointerOut={(event:ThreeEvent<PointerEvent>)=>{event.stopPropagation();onHover(null)}} onClick={(event:ThreeEvent<MouseEvent>)=>{event.stopPropagation();onChange(region)}}>
  <sphereGeometry args={[1,18,14]}/><meshBasicMaterial transparent opacity={0} colorWrite={false} depthWrite={false}/>
 </mesh>
}

function createRegionHighlight(){
 const material=new MeshBasicMaterial({color:'#ff0000',transparent:true,opacity:0,blending:NormalBlending,depthWrite:false,depthTest:true,polygonOffset:true,polygonOffsetFactor:-1,polygonOffsetUnits:-1,side:DoubleSide,toneMapped:false});
 material.userData.regionIndex=labels.indexOf('chest');
 material.onBeforeCompile=shader=>{
  shader.uniforms.uBodyRegion={value:material.userData.regionIndex};
  material.userData.shader=shader;
  shader.vertexShader=shader.vertexShader
   .replace('#include <common>','#include <common>\nvarying vec3 vBodyPosition;')
   .replace('#include <begin_vertex>','#include <begin_vertex>\nvBodyPosition=position;');
  shader.fragmentShader=shader.fragmentShader
   .replace('#include <common>','#include <common>\nvarying vec3 vBodyPosition;\nuniform int uBodyRegion;')
   .replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
if(uBodyRegion==0&&vBodyPosition.y<.79)discard;
if(uBodyRegion==1&&(vBodyPosition.y<.58||vBodyPosition.y>.8||abs(vBodyPosition.x)>.2))discard;
if(uBodyRegion==2&&(vBodyPosition.y<.38||vBodyPosition.y>.58||abs(vBodyPosition.x)>.23))discard;
if(uBodyRegion==3&&(vBodyPosition.y<.29||vBodyPosition.y>.79||abs(vBodyPosition.x)<.17))discard;
if(uBodyRegion==4&&(vBodyPosition.y>.4||abs(vBodyPosition.x)>.24))discard;`);
 };
 material.customProgramCacheKey=()=>`rocketpulse-body-region-highlight-v1`;
 const update=(region:BodyRegion,hovered:boolean)=>{
  const regionIndex=labels.indexOf(region);
  material.userData.regionIndex=regionIndex;
  material.color.set('#ff0000');
  material.opacity=hovered?.72:0;
  const shader=material.userData.shader;
  if(shader)shader.uniforms.uBodyRegion.value=regionIndex;
 };
 return {material,update};
}

function Astronaut({source,selected,hovered,crewMemberId,onSelect,onHover}:{source:Group|null;selected:BodyRegion;hovered:BodyRegion|null;crewMemberId:string;onSelect:(region:BodyRegion)=>void;onHover:(region:BodyRegion|null)=>void}){
 const groupRef=useRef<Group|null>(null);
 const normalizedSource=useMemo(()=>{
  if(!source)return null;
  const clone=source.clone(true);
  const bounds=new Box3().setFromObject(clone);
  const size=bounds.getSize(new Vector3());
  const center=bounds.getCenter(new Vector3());
  if(bounds.isEmpty()||!Number.isFinite(size.y)||size.y===0)throw new Error('Astronaut FBX has invalid geometry bounds.');
  const scale=3.2/size.y;
  clone.scale.setScalar(scale);
  clone.position.set(-center.x*scale,-center.y*scale,-center.z*scale);
  return clone;
 },[source]);
 const model=useMemo(()=>{
  if(!normalizedSource)return null;
  const clone=normalizedSource.clone(true);
  const highlight=createRegionHighlight();
  const suitTint=new Color(getCrewSuitColor(crewMemberId));
  const materials:Material[]=[];
  const meshes:Mesh[]=[];
  clone.traverse(object=>{if(object instanceof Mesh)meshes.push(object)});
  meshes.forEach(mesh=>{
   const sourceMaterials=Array.isArray(mesh.material)?mesh.material:[mesh.material];
   const crewMaterials=sourceMaterials.map(sourceMaterial=>{
    const material=sourceMaterial.clone();
    if((material.name.startsWith('01 | Suit')||material.name.startsWith('02 | Shell'))&&hasColor(material))material.color.lerp(suitTint,.82).multiplyScalar(.68);
    materials.push(material);
    return material;
   });
   mesh.material=Array.isArray(mesh.material)?crewMaterials:crewMaterials[0];
   const overlay=new Mesh(mesh.geometry,highlight.material);
   overlay.position.copy(mesh.position);
   overlay.quaternion.copy(mesh.quaternion);
   overlay.scale.copy(mesh.scale);
   overlay.name=`${mesh.name}-body-region-highlight`;
   overlay.renderOrder=1;
   mesh.parent?.add(overlay);
  });
  return {scene:clone,highlightMaterial:highlight.material,updateHighlight:highlight.update,materials};
 },[normalizedSource,crewMemberId]);
 useEffect(()=>()=>{model?.highlightMaterial.dispose();model?.materials.forEach(material=>material.dispose())},[model]);
 useEffect(()=>{model?.updateHighlight(hovered??selected,hovered!==null)},[model,selected,hovered]);
 const handlePointerMove=(event:ThreeEvent<PointerEvent>)=>{
  const hotspotRegion=labels.find(region=>event.object.name===`body-hotspot-${region}`);
  if(hotspotRegion){onHover(hotspotRegion);return}
  const point=groupRef.current?.worldToLocal(event.point.clone());
  if(!point)return;
  let closestRegion:BodyRegion='head';
  let closestDistance=Infinity;
  labels.forEach(region=>zones[region].forEach(zone=>{
   const dx=(point.x-zone.position[0])/zone.scale[0];
   const dy=(point.y-zone.position[1])/zone.scale[1];
   const dz=(point.z-zone.position[2])/zone.scale[2];
   const distance=dx*dx+dy*dy+dz*dz;
   if(distance<closestDistance){closestDistance=distance;closestRegion=region}
  }));
  onHover(closestRegion);
 };
 if(!model)return null;
 return <Float speed={.28} rotationIntensity={.05} floatIntensity={.06}><group ref={groupRef} onPointerMove={handlePointerMove} onPointerOut={()=>onHover(null)}>
  <primitive object={model.scene}/>
  {labels.flatMap(region=>zones[region].map((zone,index)=><BodyHotspot key={`${region}-${index}`} zone={zone} region={region} onChange={onSelect} onHover={onHover}/>))}
 </group></Float>
}

export default function AstronautScene({region,onChange,crewMemberId,compact=false}:{region:BodyRegion;onChange:(region:BodyRegion)=>void;crewMemberId:string;compact?:boolean}){
 const [cameraKey,setCameraKey]=useState(0);
 const [quality,setQuality]=useState<'standard'|'low'>('standard');
 const [model,setModel]=useState<Group|null>(null);
 const [modelError,setModelError]=useState<string|null>(null);
 const [hoveredRegion,setHoveredRegion]=useState<BodyRegion|null>(null);
 useEffect(()=>{
  let active=true;
  new FBXLoader().load(suitModelUrl,loadedModel=>{if(active)setModel(loadedModel)},undefined,error=>{if(active)setModelError(error instanceof Error?error.message:'Unable to load the astronaut model.')});
  return ()=>{active=false};
 },[]);
 return <div className={`astronaut-stage ${compact?'stage-small':''}`} data-hovered-region={hoveredRegion??undefined}>
  <div className="stage-topline"><span><Scan size={13}/> SPACE EXPLORATION / CREW MODEL</span><span>DRAG TO ORBIT · SCROLL TO ZOOM</span></div>
  {!model||modelError?<div className="model-load-status" role={modelError?'alert':'status'}>{modelError?'Astronaut model failed to load.': 'Loading astronaut model…'}</div>:null}
  <Canvas key={cameraKey} camera={{position:[.1,.1,5.55],fov:43}} dpr={quality==='standard'?[1,1.6]:1} gl={{alpha:true,antialias:quality==='standard'}} fallback={<div className="stage-fallback">WebGL unavailable — use the body region controls below.</div>}>
   <color attach="background" args={['#000000']}/>
   <SpaceBackdrop/>
   <ambientLight intensity={1.6}/>
   <directionalLight position={[3,5,6]} intensity={3.1} color="#ffe5be"/>
   <pointLight position={[-3,0,3]} intensity={2.9} color="#4a9bb8"/>
   <Astronaut source={model} selected={region} hovered={hoveredRegion} crewMemberId={crewMemberId} onSelect={onChange} onHover={setHoveredRegion}/>
   <OrbitControls enablePan={false} minDistance={3.3} maxDistance={8.5} maxPolarAngle={Math.PI*.8}/>
  </Canvas>
  <div className="stage-bottom">
   <div className="region-selector">{labels.map(bodyRegion=><button key={bodyRegion} type="button" className={region===bodyRegion?'region-choice selected':'region-choice'} onMouseEnter={()=>setHoveredRegion(bodyRegion)} onMouseLeave={()=>setHoveredRegion(null)} onClick={()=>onChange(bodyRegion)} aria-pressed={region===bodyRegion}>{bodyRegion.toUpperCase()}</button>)}</div>
   <div className="stage-controls">
    <button onClick={()=>setCameraKey(value=>value+1)} title="Reset camera" aria-label="Reset camera"><RotateCcw size={13}/></button>
    <button onClick={()=>setQuality(value=>value==='standard'?'low':'standard')} title="Toggle rendering quality">{quality.toUpperCase()}</button>
   </div>
  </div>
 </div>
}
