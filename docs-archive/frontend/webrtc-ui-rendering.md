# 视频流与轨道的 DOM 挂载

> 路径：相关的 WebRTC 与 `VideoPlayer.tsx` 类似组件区

## 1. 原生 DOM 与 React 的拉扯
React 是一个建立在虚拟 DOM (VDOM) 渲染和比对哲学上的引擎。但这对于一块从 `MediaStream` 生拉硬拽出来的底层媒体轨道极其致命！
如果任由原生的 `<video>` 组件在发生状态改变（例如改变面板大小等触发上层重绘时）顺其自然地跟随 React 管线去重刷属性：
**整条视频轨 (SRC Object) 极易被干碎或脱落销毁。造成你看着画面一弹、黑屏后死守着白圈在转！**

## 2. 手动接管 `srcObject`
所有的流媒体播放容器均强制使用了极其防守式的 `useRef` + `useEffect` 强隔离：
- React 只管负责画出一个 `<video ref={videoRef} autoPlay playsInline muted />` 并任由其渲染结束脱手。
- 接下来的数据强行塞入：不论从由于云桥握手触发 `track` 事件拿到 `e.streams[0]`，我们立刻在 Effect 中直接执行底层的 `videoRef.current.srcObject = stream`。规避了在顶端依赖对象导致疯狂闪退触发重绑的操作。

## 3. UI 布局与硬截屏适应性
因为远端的画面千奇百怪（例如你接了个极地竖屏的手机，又去截了个宽屏的桌显）：
我们使用极其严苛的 CSS `object-fit: contain` 或 `scale-down` 来保底处理物理显示与容器宽度的适配。
同时这使得不论是悬挂在全局或者通过快捷键拽出为桌面独立画中画（PiP - Picture In Picture），媒体流轨对象永远挂载生效而不掉片。
