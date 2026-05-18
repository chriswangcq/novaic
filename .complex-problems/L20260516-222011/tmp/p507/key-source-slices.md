# P507 key source slices

## task_queue/sagas/wake_finalize.py
     1	"""
     2	WakeFinalize Saga — close the current wake after the active stack drains.
     3	
     4	Flow:
     5	1. Structural Cortex scope_end (archive to /ro/scopes/ without summary)
     6	2. Notify Session Coordinator with the expected session generation
     7	3. Set SubAgent state: sleeping (main) or completed (sub), gated by step 2
     8	
     9	This saga is runtime cleanup only. It never creates ``summary.md`` and never
    10	derives continuity from chat output. Durable folded summaries are produced
    11	only when the LLM closes the current stack-top scope through
    12	``skill_end(report=...)``.
    13	"""
    14	
    15	from ..saga import SagaDefinition
    16	from . import register_saga_definition
    17	from ..contracts.session_generation import require_positive_session_generation
    18	from ..topics import TaskTopics
    19	
    20	
    21	def _is_sub_subagent(subagent_id: str) -> bool:
    22	    return subagent_id.startswith("sub-")
    23	
    24	
    25	def _build_cortex_scope_end_payload(ctx):
    26	    """Feed finalize_reason + round_num into archival for audit logs.
    27	
    28	    Structural scope_end gets an empty report. It is not a summary path.
    29	    """
    30	    return {
    31	        "scope_id": ctx["scope_id"],
    32	        "agent_root_scope_id": ctx.get("agent_root_scope_id"),
    33	        "wake_scope_path": ctx.get("wake_scope_path"),
    34	        "agent_id": ctx["agent_id"],
    35	        "user_id": ctx.get("user_id", ""),
    36	        "session_generation": _session_generation(ctx),
    37	        "report": "",
    38	        "finalize_reason": ctx.get("finalize_reason", "stack_empty"),
    39	        "remaining_stack": _remaining_stack_snapshot(ctx),
    40	        "round_num": _non_negative_int(ctx.get("round_num"), "round_num"),
    41	    }
    42	
    43	
    44	def _build_set_sleeping_payload(ctx):
    45	    return {
    46	        "agent_id": ctx["agent_id"],
    47	        "subagent_id": ctx["subagent_id"],
    48	        **_subagent_terminal_status_identity(ctx),
    49	    }
    50	
    51	
    52	def _build_set_subagent_completed_payload(ctx):
    53	    """Completion is lifecycle only. Child-to-parent substance is sent
    54	    explicitly through Environment IM before this finalize step.
    55	    """
    56	    return {
    57	        "agent_id": ctx["agent_id"],
    58	        "subagent_id": ctx["subagent_id"],
    59	        **_subagent_terminal_status_identity(ctx),
    60	        "result": None,
    61	    }
    62	
    63	
    64	def _should_set_sleeping(ctx) -> bool:
    65	    return not _is_sub_subagent(ctx.get("subagent_id", "main"))
    66	
    67	
    68	def _should_set_completed(ctx) -> bool:
    69	    return _is_sub_subagent(ctx.get("subagent_id", "main"))
    70	
    71	
    72	def _session_generation(ctx) -> int:
    73	    return require_positive_session_generation(ctx, "wake_finalize")
    74	
    75	
    76	def _non_negative_int(value, owner: str) -> int:
    77	    if value is None or value == "":
    78	        return 0
    79	    if isinstance(value, bool):
    80	        raise ValueError(f"{owner} must be a non-negative integer")
    81	    try:
    82	        parsed = int(value)
    83	    except (TypeError, ValueError) as exc:
    84	        raise ValueError(f"{owner} must be a non-negative integer") from exc
    85	    if parsed < 0:
    86	        raise ValueError(f"{owner} must be a non-negative integer")
    87	    return parsed
    88	
    89	
    90	def _subagent_terminal_status_identity(ctx):
    91	    return {
    92	        "scope_id": ctx["scope_id"],
    93	        "session_generation": _session_generation(ctx),
    94	    }
    95	
    96	
    97	def _remaining_stack_snapshot(ctx):
    98	    remaining_stack = ctx.get("remaining_stack")
    99	    if isinstance(remaining_stack, dict):
   100	        return dict(remaining_stack)
   101	    raise ValueError("remaining_stack is required for wake_finalize")
   102	
   103	
   104	def _build_session_ended_payload(ctx):
   105	    return {
   106	        "agent_id": ctx["agent_id"],
   107	        "subagent_id": ctx["subagent_id"],
   108	        "scope_id": ctx["scope_id"],
   109	        "agent_root_scope_id": ctx.get("agent_root_scope_id"),
   110	        "wake_scope_path": ctx.get("wake_scope_path"),
   111	        "finalize_reason": ctx.get("finalize_reason", "stack_empty"),
   112	        "generation": _session_generation(ctx),
   113	        "remaining_stack": _remaining_stack_snapshot(ctx),
   114	        "round_num": _non_negative_int(ctx.get("round_num"), "round_num"),
   115	    }
   116	
   117	
   118	WAKE_FINALIZE_SAGA = SagaDefinition("wake_finalize")
   119	
   120	WAKE_FINALIZE_SAGA.add_task_step(
   121	    name="cortex_scope_end",
   122	    topic=TaskTopics.CORTEX_SCOPE_END,
   123	    build_payload=_build_cortex_scope_end_payload,
   124	    optional=True,
   125	)
   126	
   127	WAKE_FINALIZE_SAGA.add_task_step(
   128	    name="session_ended",
   129	    topic=TaskTopics.SESSION_ENDED,
   130	    build_payload=_build_session_ended_payload,
   131	)
   132	
   133	WAKE_FINALIZE_SAGA.add_task_step(
   134	    name="set_subagent_sleeping",
   135	    topic=TaskTopics.SUBAGENT_SET_SLEEPING,
   136	    build_payload=_build_set_sleeping_payload,
   137	    condition=_should_set_sleeping,
   138	    depends_on=["session_ended"],
   139	)
   140	
   141	WAKE_FINALIZE_SAGA.add_task_step(
   142	    name="set_subagent_completed",
   143	    topic=TaskTopics.SUBAGENT_SET_COMPLETED,
   144	    build_payload=_build_set_subagent_completed_payload,
   145	    condition=_should_set_completed,
   146	    depends_on=["session_ended"],
   147	)
   148	
   149	WAKE_FINALIZE_SAGA = register_saga_definition(WAKE_FINALIZE_SAGA)

## task_queue/handlers/session_handlers.py
     1	"""
     2	Session Handlers — Session Coordinator interactions
     3	
     4	Topics:
     5	- session.ended: Notify Session Coordinator that a session has ended
     6	"""
     7	
     8	from typing import Dict, Any
     9	from . import register_handler
    10	from ..topics import TaskTopics
    11	from common.exceptions import BusinessError, ValidationError
    12	
    13	
    14	def _positive_generation(value: Any) -> int:
    15	    if value is None:
    16	        raise ValidationError("Missing required field: generation")
    17	    if isinstance(value, bool):
    18	        raise ValidationError("generation must be a positive integer")
    19	    if isinstance(value, int):
    20	        generation = value
    21	    elif isinstance(value, str) and value.strip().isdigit():
    22	        generation = int(value.strip())
    23	    else:
    24	        raise ValidationError("generation must be a positive integer")
    25	    if generation < 1:
    26	        raise ValidationError("generation must be a positive integer")
    27	    return generation
    28	
    29	
    30	@register_handler(TaskTopics.SESSION_ENDED)
    31	def handle_session_ended(payload: Dict[str, Any], ctx: dict) -> Dict[str, Any]:
    32	    """Notify Session Coordinator that a session has ended.
    33	
    34	    Called as the final step of the wake_finalize saga.
    35	    The Session Coordinator will either close the session or restart from the
    36	    append-only pending input projection.
    37	
    38	    Payload:
    39	        agent_id: str
    40	        subagent_id: str
    41	        scope_id: str
    42	        finalize_reason: str
    43	        generation: int
    44	        remaining_stack: dict
    45	    """
    46	    agent_id = payload.get("agent_id")
    47	    subagent_id = payload.get("subagent_id")
    48	    scope_id = payload.get("scope_id")
    49	    finalize_reason = payload.get("finalize_reason")
    50	    generation = payload.get("generation")
    51	    remaining_stack = payload.get("remaining_stack")
    52	
    53	    if not agent_id:
    54	        raise ValidationError("Missing required field: agent_id")
    55	    if not subagent_id:
    56	        raise ValidationError("Missing required field: subagent_id")
    57	    if not scope_id:
    58	        raise ValidationError("Missing required field: scope_id")
    59	    if not finalize_reason:
    60	        raise ValidationError("Missing required field: finalize_reason")
    61	    generation = _positive_generation(generation)
    62	    if remaining_stack is None:
    63	        raise ValidationError("Missing required field: remaining_stack")
    64	    if not isinstance(remaining_stack, dict):
    65	        raise ValidationError("remaining_stack must be an object")
    66	
    67	    saga_client = ctx.get("saga_client")
    68	    if not saga_client:
    69	        raise ValidationError("Missing required client in ctx: saga_client")
    70	
    71	    result = saga_client.session_ended(
    72	        agent_id=agent_id,
    73	        subagent_id=subagent_id,
    74	        scope_id=scope_id,
    75	        finalize_reason=str(finalize_reason),
    76	        generation=generation,
    77	        remaining_stack=remaining_stack,
    78	    )
    79	
    80	    if result.get("action") == "finalize_rejected":
    81	        reason = result.get("reason", "unknown")
    82	        raise BusinessError(f"session_ended finalize_rejected: {reason}")
    83	
    84	    return {
    85	        "success": True,
    86	        "action": result.get("action", "session_closed"),
    87	        "scope_id": scope_id,
    88	        "new_saga_id": result.get("saga_id"),
    89	        "new_scope_id": result.get("scope_id"),
    90	    }

## queue_service/session_repo.py session_ended
   500	        return result
   501	
   502	    def session_ended(
   503	        self,
   504	        agent_id: str,
   505	        subagent_id: str,
   506	        scope_id: str,
   507	        *,
   508	        finalize_reason: Optional[str] = None,
   509	        generation: Optional[int] = None,
   510	        remaining_stack: Dict[str, Any],
   511	    ) -> Dict[str, Any]:
   512	        """Clean up session and optionally restart from pending inbox.
   513	
   514	        Returns:
   515	            {"action": "session_closed"}
   516	            or {"action": "restart_pending", "scope_id": ..., "outbox_id": ...}
   517	        """
   518	        session_key = f"{agent_id}:{subagent_id}"
   519	        now = self._clock()
   520	        if not (finalize_reason or "").strip():
   521	            raise ValueError("finalize_reason is required for session finalize")
   522	        if remaining_stack is None:
   523	            raise ValueError("remaining_stack is required for session finalize")
   524	        finalize_generation = _require_positive_generation(generation, "session finalize")
   525	        finalize_metadata = {
   526	            "finalize_reason": finalize_reason,
   527	            "finalize_generation": finalize_generation,
   528	            "remaining_stack": dict(remaining_stack),
   529	            "ended_scope_id": scope_id,
   530	        }
   531	
   532	        # Step 1: finalize the active generation and derive restart source from inbox.
   533	        with self.db.transaction(lock_type="global"):
   534	            current_state = self.session_ledger.get_state(session_key)
   535	            finalize_decision = decide_session_finalize(SessionFinalizeInput(
   536	                state=self._runtime_state_from_session_state(current_state),
   537	                scope_id=scope_id,
   538	                finalize_generation=finalize_generation,
   539	            ))
   540	            if finalize_decision.action is SessionFinalizeAction.REJECT_FINALIZE:
   541	                result = finalize_decision.result
   542	                self.session_ledger.record_session_finalize_rejected(
   543	                    session_key=session_key,
   544	                    agent_id=agent_id,
   545	                    subagent_id=subagent_id,
   546	                    user_id=current_state.get("user_id") if current_state else None,
   547	                    event_generation=finalize_decision.event_generation,
   548	                    finalize_metadata=finalize_metadata,
   549	                    result=result,
   550	                    scope_id=scope_id,
   551	                    finalize_generation=finalize_generation,
   552	                    finalize_reason=finalize_reason,
   553	                    rejection_reason=finalize_decision.reason,
   554	                    created_at=now,
   555	                )
   556	                return result
   557	
   558	            event_generation = finalize_decision.event_generation
   559	            self.session_ledger.record_session_finalized(
   560	                session_key=session_key,
   561	                agent_id=agent_id,
   562	                subagent_id=subagent_id,
   563	                user_id=current_state.get("user_id") if current_state else None,
   564	                active_saga_id=(
   565	                    current_state.get("active_saga_id")
   566	                    if current_state else None
   567	                ),
   568	                active_scope_id=(
   569	                    current_state.get("active_scope_id")
   570	                    if current_state else None
   571	                ),
   572	                event_generation=event_generation,
   573	                finalize_metadata=finalize_metadata,
   574	                scope_id=scope_id,
   575	                finalize_reason=finalize_reason,
   576	                created_at=now,
   577	            )
   578	
   579	            pending_projection = build_pending_input_projection(
   580	                self.session_ledger.list_unconsumed_input_events(session_key)
   581	            )
   582	            self._record_pending_projection_in_current_transaction(
   583	                session_key=session_key,
   584	                agent_id=agent_id,
   585	                subagent_id=subagent_id,
   586	                user_id=pending_projection.get("user_id") if pending_projection else None,
   587	                active_scope_id=None,
   588	                marker=f"session_ended:{session_key}:{scope_id}",
   589	                created_at=now,
   590	            )
   591	
   592	            if not pending_projection:
   593	                logger.info(
   594	                    "[SessionCoordinator] session_ended closed: %s scope=%s",
   595	                    session_key, scope_id,
   596	                )
   597	                result = {"action": "session_closed"}
   598	                self._record_session_transition_in_current_transaction(
   599	                    event_type=SessionEventType.SESSION_CLOSED.value,
   600	                    event_key=session_event_key(
   601	                        SessionEventKeyPrefix.SESSION_CLOSED,
   602	                        session_key,
   603	                        scope_id,
   604	                    ),
   605	                    agent_id=agent_id,
   606	                    subagent_id=subagent_id,
   607	                    user_id=None,
   608	                    trigger_type=None,
   609	                    metadata=finalize_metadata,
   610	                    result=result,
   611	                    state=SessionRuntimeStatus.NO_ACTIVE.value,
   612	                    active_saga_id=None,
   613	                    active_scope_id=None,
   614	                    created_at=now,
   615	                )
   616	                return result
   617	
   618	            pending = pending_restart_source_from_projection(
   619	                session_key=session_key,
   620	                agent_id=agent_id,
   621	                subagent_id=subagent_id,
   622	                projection=pending_projection,
   623	            )
   624	
   625	            new_scope_id = self._new_scope_id()
   626	            session_generation = self.session_ledger.next_generation(session_key)
   627	            restart_plan = build_restart_wake_plan(
   628	                session_key=session_key,
   629	                pending=pending,
   630	                scope_id=new_scope_id,
   631	                session_generation=session_generation,
   632	                finalize_metadata=finalize_metadata,
   633	                pending_input_event_ids=list(
   634	                    pending_projection.get("input_event_ids") or []
   635	                ),
   636	            )
   637	            logger.info(
   638	                "[SessionCoordinator] session_ended queued restart: %s scope=%s trigger=%s",
   639	                session_key, new_scope_id, pending["trigger_type"],
   640	            )
   641	            result = {
   642	                "action": QueueFinalizeAction.RESTART_PENDING.value,
   643	                "scope_id": new_scope_id,
   644	                "delivery": "outbox_pending",
   645	            }
   646	            outbox_ids = self._record_session_transition_in_current_transaction(
   647	                event_type=SessionEventType.SESSION_RESTART_PENDING.value,
   648	                event_key=session_event_key(
   649	                    SessionEventKeyPrefix.SESSION_RESTART_PENDING,
   650	                    restart_plan.outbox_effect["idempotency_key"],

## queue_service/saga_repo.py compensation
  1110	            claimed_by=projection.get("claimed_by"),
  1111	            heartbeat_at=projection.get("heartbeat_at"),
  1112	            updated_at=str(projection.get("updated_at") or updated_at),
  1113	        ))
  1114	
  1115	    def _subtract_seconds(self, now: str, seconds: int) -> str:
  1116	        now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
  1117	        return (now_dt - timedelta(seconds=int(seconds))).isoformat().replace("+00:00", "Z")
  1118	
  1119	
  1120	# Saga types that need wake_finalize compensation on failure
  1121	_WAKE_SAGA_TYPES = ("subagent_wake", "react_think", "react_actions")
  1122	
  1123	
  1124	def _positive_session_generation_from_context(context: Dict[str, Any]) -> int | None:
  1125	    raw = context.get("session_generation")
  1126	    if isinstance(raw, bool):
  1127	        return None
  1128	    if isinstance(raw, int):
  1129	        generation = raw
  1130	    elif isinstance(raw, str) and raw.strip():
  1131	        try:
  1132	            generation = int(raw.strip())
  1133	        except ValueError:
  1134	            return None
  1135	    else:
  1136	        return None
  1137	    return generation if generation > 0 else None
  1138	
  1139	
  1140	def _explicit_or_unknown_remaining_stack(context: Dict[str, Any]) -> dict[str, Any]:
  1141	    remaining_stack = context.get("remaining_stack")
  1142	    if isinstance(remaining_stack, dict):
  1143	        return dict(remaining_stack)
  1144	    return {"known": False, "depth": 0, "frames": []}
  1145	
  1146	
  1147	class SagaOrchestrator(SagaRepository):
  1148	    """
  1149	    Saga lifecycle coordinator for queue-service-owned failure handling.
  1150	    """
  1151	    
  1152	    def __init__(
  1153	        self,
  1154	        queue,
  1155	        db,
  1156	        *,
  1157	        clock: Callable[[], str],
  1158	        saga_id_provider: Callable[[], str],
  1159	            session_ledger: SessionLedgerRepository | None = None,
  1160	            saga_ledger: SagaLedgerRepository | None = None,
  1161	            lease_ledger: LeaseLedgerRepository | None = None,
  1162	            max_outbox_attempts: int = 10,
  1163	    ):
  1164	        super().__init__(
  1165	            db,
  1166	            queue,
  1167	                clock=clock,
  1168	                saga_id_provider=saga_id_provider,
  1169	                saga_ledger=saga_ledger,
  1170	                lease_ledger=lease_ledger,
  1171	            )
  1172	        self._session_ledger = session_ledger or SessionLedgerRepository(
  1173	            db,
  1174	            clock=clock,
  1175	            event_id_provider=_missing_session_event_id,
  1176	            outbox_id_provider=_missing_session_outbox_id,
  1177	        )
  1178	        self._max_outbox_attempts = int(max_outbox_attempts)
  1179	    
  1180	    def mark_failed(self, saga_id: str, error: str):
  1181	        """Mark failed and persist compensation intent as saga outbox effects.
  1182	
  1183	        Three cases:
  1184	          1. WAKE/think/actions saga fails → enqueue wake_finalize creation.
  1185	          2. wake_finalize itself fails → enqueue session suspected-dead event.
  1186	          3. Everything else → just record status.
  1187	        """
  1188	        saga = self.get(saga_id)
  1189	        saga_type = saga.get("saga_type") if saga else None
  1190	        ctx = (saga or {}).get("context") or {}
  1191	        if isinstance(ctx, str):
  1192	            try:
  1193	                ctx = json.loads(ctx)
  1194	            except (json.JSONDecodeError, TypeError):
  1195	                ctx = {}
  1196	
  1197	        effects: list[dict[str, Any]] = []
  1198	        if saga and saga_type in _WAKE_SAGA_TYPES:
  1199	            effect = self._build_wake_finalize_compensation_effect(
  1200	                saga_id=saga_id,
  1201	                saga_type=str(saga_type),
  1202	                context=ctx,
  1203	            )
  1204	            if effect:
  1205	                effects.append(effect)
  1206	        elif saga and saga_type == "wake_finalize":
  1207	            effect = self._build_session_suspected_dead_effect(
  1208	                saga_id=saga_id,
  1209	                error=error,
  1210	                context=ctx,
  1211	            )
  1212	            if effect:
  1213	                effects.append(effect)
  1214	
  1215	        super().mark_failed(saga_id, error, effects=effects)
  1216	
  1217	    def drain_pending_effects(
  1218	        self,
  1219	        *,
  1220	        saga_id: str | None = None,
  1221	        effect_types: list[str] | None = None,
  1222	        limit: int = 50,
  1223	    ) -> dict[str, int]:
  1224	        """Publish committed saga outbox effects through boundary adapters."""
  1225	        selected_effect_types = effect_types or [
  1226	            "create_wake_finalize_saga",
  1227	            "record_session_suspected_dead",
  1228	        ]
  1229	        result = {"published": 0, "failed": 0, "dead_letter": 0}
  1230	        pending = self._saga_ledger.list_pending_outbox(
  1231	            saga_id=saga_id,
  1232	            effect_types=selected_effect_types,
  1233	            limit=limit,
  1234	        )
  1235	        for effect in pending:
  1236	            outbox_id = str(effect["id"])
  1237	            try:
  1238	                self._publish_saga_outbox_effect(effect)
  1239	            except Exception as exc:
  1240	                status = self._saga_ledger.mark_outbox_failed(
  1241	                    outbox_id,
  1242	                    error=str(exc),
  1243	                    failed_at=self._now(),
  1244	                    max_attempts=self._max_outbox_attempts,
  1245	                )
  1246	                if status == "dead_letter":
  1247	                    result["dead_letter"] += 1
  1248	                else:
  1249	                    result["failed"] += 1
  1250	                logging.getLogger(__name__).warning(
  1251	                    "[SagaOrchestrator] saga outbox effect failed: id=%s type=%s error=%s",
  1252	                    outbox_id,
  1253	                    effect.get("effect_type"),
  1254	                    exc,
  1255	                )
  1256	                continue
  1257	            self._saga_ledger.mark_outbox_published(
  1258	                outbox_id,
  1259	                published_at=self._now(),
  1260	            )
  1261	            result["published"] += 1
  1262	        return result
  1263	
  1264	    def _publish_saga_outbox_effect(self, effect: dict[str, Any]) -> None:
  1265	        effect_type = str(effect["effect_type"])
  1266	        payload = dict(effect.get("payload") or {})
  1267	        if effect_type == "create_wake_finalize_saga":
  1268	            self.create(
  1269	                saga_type=str(payload["saga_type"]),
  1270	                context=dict(payload["context"]),
  1271	                idempotency_key=str(payload["idempotency_key"]),
  1272	            )
  1273	            return
  1274	        if effect_type == "record_session_suspected_dead":
  1275	            self._record_session_suspected_dead_event(**payload)
  1276	            return
  1277	        raise ValueError(f"unsupported saga outbox effect_type: {effect_type}")
  1278	
  1279	    def _build_wake_finalize_compensation_effect(
  1280	        self,
  1281	        *,
  1282	        saga_id: str,
  1283	        saga_type: str,
  1284	        context: Dict[str, Any],
  1285	    ) -> dict[str, Any] | None:
  1286	        scope_id = context.get("scope_id")
  1287	        agent_id = context.get("agent_id")
  1288	        session_generation = _positive_session_generation_from_context(context)
  1289	        if not scope_id or not agent_id or session_generation is None:
  1290	            return None
  1291	        finalize_context = {
  1292	            "scope_id": scope_id,
  1293	            "agent_id": agent_id,
  1294	            "subagent_id": context.get("subagent_id", "main"),
  1295	            "user_id": context.get("user_id", ""),
  1296	            "session_generation": session_generation,
  1297	            "finalize_reason": f"compensation:{saga_type}_failed",
  1298	            "remaining_stack": _explicit_or_unknown_remaining_stack(context),
  1299	        }
  1300	        for key in (
  1301	            "agent_root_scope_id",
  1302	            "wake_scope_path",
  1303	            "round_num",
  1304	        ):
  1305	            if key in context:
  1306	                finalize_context[key] = context[key]
  1307	        idempotency_key = f"wake-finalize-{scope_id}-comp"
  1308	        return {
  1309	            "effect_type": "create_wake_finalize_saga",
  1310	            "payload": {
  1311	                "saga_type": "wake_finalize",
  1312	                "context": finalize_context,
  1313	                "idempotency_key": idempotency_key,
  1314	            },
  1315	            "idempotency_key": f"saga-compensation:{saga_id}:wake_finalize",
  1316	        }
  1317	
  1318	    def _build_session_suspected_dead_effect(
  1319	        self,
  1320	        *,
  1321	        saga_id: str,
  1322	        error: str,
  1323	        context: Dict[str, Any],
  1324	    ) -> dict[str, Any] | None:
  1325	        agent_id = context.get("agent_id")
  1326	        subagent_id = context.get("subagent_id", "main")
  1327	        if not agent_id or not subagent_id:
  1328	            return None
  1329	        session_key = f"{agent_id}:{subagent_id}"
  1330	        return {
  1331	            "effect_type": "record_session_suspected_dead",
  1332	            "payload": {
  1333	                "session_key": session_key,
  1334	                "agent_id": agent_id,
  1335	                "subagent_id": subagent_id,
  1336	                "user_id": context.get("user_id", ""),
  1337	                "failed_scope_id": context.get("scope_id"),
  1338	                "failed_saga_id": saga_id,
  1339	                "error": error,
  1340	                "saga_context": dict(context),
  1341	            },
  1342	            "idempotency_key": f"suspected:{session_key}:{saga_id}",
  1343	        }
  1344	
  1345	    def _record_session_suspected_dead_event(
  1346	        self,
  1347	        *,
  1348	        session_key: str,
  1349	        agent_id: str,
  1350	        subagent_id: str,
  1351	        user_id: str,
  1352	        failed_scope_id: Optional[str],
  1353	        failed_saga_id: str,
  1354	        error: str,
  1355	        saga_context: Dict[str, Any],
  1356	    ) -> str:
  1357	        event_id = f"suspected:{session_key}:{failed_saga_id}"
  1358	        recovery_id = f"recovery:{session_key}:{failed_scope_id or failed_saga_id}"
  1359	        now = self._now()
  1360	        payload = {
  1361	            "recovery_id": recovery_id,
  1362	            "reason": "wake_finalize_failed",
  1363	            "error": error,
  1364	            "failed_scope_id": failed_scope_id,
  1365	            "failed_saga_id": failed_saga_id,
  1366	            "finalize_reason": saga_context.get(
  1367	                "finalize_reason",
  1368	                "wake_finalize_failed",
  1369	            ),
  1370	            "force_archive_required": True,
  1371	            "wake_scope_path": saga_context.get("wake_scope_path"),
  1372	            "agent_root_scope_id": saga_context.get("agent_root_scope_id"),
  1373	            "round_num": saga_context.get("round_num", 0),
  1374	            "remaining_stack": _explicit_or_unknown_remaining_stack(saga_context),
  1375	            "user_id": user_id,
  1376	        }
  1377	        with self.db.transaction(lock_type="global"):
  1378	            state = self._session_ledger.get_state(session_key)
  1379	            if not state:
  1380	                raise RuntimeError(
  1381	                    "cannot record session_suspected_dead without session state"
  1382	                )
  1383	            generation = require_positive_session_generation_value(
  1384	                state.get("generation"),
  1385	                "record_session_suspected_dead",
  1386	            )
  1387	            self._session_ledger.append_event(
  1388	                session_key=session_key,
  1389	                agent_id=agent_id,
  1390	                subagent_id=subagent_id,
  1391	                user_id=user_id,
  1392	                generation=generation,
  1393	                event_type=SessionEventType.SESSION_SUSPECTED_DEAD.value,
  1394	                payload=payload,
  1395	                causation_id=failed_saga_id,

## queue_service/session_recovery.py
     1	"""Pure recovery shaping helpers for Queue sessions."""
     2	
     3	from __future__ import annotations
     4	
     5	import json
     6	from collections.abc import Mapping
     7	from dataclasses import dataclass
     8	from typing import Any
     9	
    10	from common.wake.trigger_types import TriggerType
    11	
    12	_MISSING = object()
    13	
    14	
    15	def _unknown_remaining_stack() -> dict[str, Any]:
    16	    return {"known": False, "depth": 0, "frames": []}
    17	
    18	
    19	def _positive_session_generation(raw: Any) -> int | None:
    20	    if isinstance(raw, bool):
    21	        return None
    22	    if isinstance(raw, int):
    23	        generation = raw
    24	    elif isinstance(raw, str) and raw.strip():
    25	        try:
    26	            generation = int(raw.strip())
    27	        except ValueError:
    28	            return None
    29	    else:
    30	        return None
    31	    return generation if generation > 0 else None
    32	
    33	
    34	def _non_negative_int(raw: Any, owner: str) -> int:
    35	    if raw is None or raw == "":
    36	        return 0
    37	    if isinstance(raw, bool):
    38	        raise ValueError(f"{owner} must be a non-negative integer")
    39	    if isinstance(raw, int):
    40	        value = raw
    41	    elif isinstance(raw, str) and raw.strip():
    42	        try:
    43	            value = int(raw.strip())
    44	        except ValueError as exc:
    45	            raise ValueError(f"{owner} must be a non-negative integer") from exc
    46	    else:
    47	        raise ValueError(f"{owner} must be a non-negative integer")
    48	    if value < 0:
    49	        raise ValueError(f"{owner} must be a non-negative integer")
    50	    return value
    51	
    52	
    53	@dataclass(frozen=True)
    54	class RecoveryDispatch:
    55	    trigger_type: str
    56	    metadata: dict[str, Any]
    57	
    58	
    59	def recovery_marker_from_suspected_dead_event(
    60	    *,
    61	    session_key: str,
    62	    agent_id: str,
    63	    subagent_id: str,
    64	    user_id: str,
    65	    event: Mapping[str, Any],
    66	) -> dict[str, Any]:
    67	    """Build a recovery marker from an explicit suspected-dead event."""
    68	
    69	    payload = dict(event.get("payload") or {})
    70	    failed_scope_id = payload.get("failed_scope_id")
    71	    failed_saga_id = payload.get("failed_saga_id")
    72	    recovery_id = (
    73	        payload.get("recovery_id")
    74	        or f"recovery:{session_key}:{failed_scope_id or event.get('id')}"
    75	    )
    76	    marker = {
    77	        "id": recovery_id,
    78	        "session_key": session_key,
    79	        "agent_id": agent_id,
    80	        "subagent_id": subagent_id,
    81	        "user_id": payload.get("user_id") or user_id,
    82	        "failed_scope_id": failed_scope_id,
    83	        "failed_saga_id": failed_saga_id,
    84	        "reason": payload.get("reason") or "wake_finalize_failed",
    85	        "metadata": json.dumps(
    86	            payload,
    87	            ensure_ascii=False,
    88	            sort_keys=True,
    89	        ),
    90	        "created_at": event.get("created_at"),
    91	        "source_event_id": event.get("id"),
    92	    }
    93	    session_generation = _positive_session_generation(event.get("generation"))
    94	    if session_generation is not None:
    95	        marker["session_generation"] = session_generation
    96	    return marker
    97	
    98	
    99	def build_recovery_dispatch(
   100	    *,
   101	    original_trigger_type: str,
   102	    input_metadata: Mapping[str, Any] | None,
   103	    recovery_marker: Mapping[str, Any],
   104	    pending_projection: Mapping[str, Any] | None,
   105	) -> RecoveryDispatch:
   106	    """Build dispatch trigger/metadata for a recovered wake."""
   107	
   108	    if pending_projection:
   109	        metadata = dict(pending_projection.get("metadata") or {})
   110	        metadata["recovery_pending_input_event_ids"] = list(
   111	            pending_projection.get("input_event_ids") or []
   112	        )
   113	    else:
   114	        metadata = dict(input_metadata or {})
   115	
   116	    recovery_metadata = _decode_json_dict(recovery_marker.get("metadata"))
   117	    metadata.update({
   118	        "original_trigger_type": original_trigger_type,
   119	        "recovery_id": recovery_marker.get("id"),
   120	        "recovery_reason": recovery_marker.get("reason"),
   121	        "recovery_from_scope_id": recovery_marker.get("failed_scope_id"),
   122	        "recovery_failed_saga_id": recovery_marker.get("failed_saga_id"),
   123	        "force_archive_required": True,
   124	        "recovery": {
   125	            "id": recovery_marker.get("id"),
   126	            "reason": recovery_marker.get("reason"),
   127	            "failed_scope_id": recovery_marker.get("failed_scope_id"),
   128	            "failed_saga_id": recovery_marker.get("failed_saga_id"),
   129	            "metadata": recovery_metadata,
   130	        },
   131	    })
   132	    if recovery_marker.get("source_event_id"):
   133	        metadata["recovery_suspected_dead_event_id"] = (
   134	            recovery_marker["source_event_id"]
   135	        )
   136	
   137	    return RecoveryDispatch(
   138	        trigger_type=TriggerType.RECOVERED.value,
   139	        metadata=metadata,
   140	    )
   141	
   142	
   143	def build_recovery_archive_effect(
   144	    *,
   145	    recovery_marker: Mapping[str, Any],
   146	    agent_id: str,
   147	    user_id: str,
   148	    effect_type: str,
   149	) -> dict[str, Any] | None:
   150	    """Build the durable archive effect for a failed wake scope."""
   151	
   152	    failed_scope_id = recovery_marker.get("failed_scope_id")
   153	    session_generation = _positive_session_generation(
   154	        recovery_marker.get("session_generation")
   155	    )
   156	    if not failed_scope_id or session_generation is None:
   157	        return None
   158	
   159	    recovery_metadata = _decode_json_dict(recovery_marker.get("metadata"))
   160	    raw_remaining_stack = recovery_metadata.get("remaining_stack", _MISSING)
   161	    if raw_remaining_stack is _MISSING:
   162	        remaining_stack = _unknown_remaining_stack()
   163	    elif isinstance(raw_remaining_stack, dict):
   164	        remaining_stack = dict(raw_remaining_stack)
   165	    else:
   166	        raise ValueError("remaining_stack must be an object")
   167	    return {
   168	        "effect_type": effect_type,
   169	        "payload": {
   170	            "scope_id": failed_scope_id,
   171	            "agent_root_scope_id": recovery_metadata.get("agent_root_scope_id"),
   172	            "wake_scope_path": recovery_metadata.get("wake_scope_path"),
   173	            "agent_id": agent_id,
   174	            "user_id": recovery_marker.get("user_id") or user_id,
   175	            "session_generation": session_generation,
   176	            "report": "",
   177	            "finalize_reason": (
   178	                f"recovery:{recovery_marker.get('reason') or 'unknown'}"
   179	            ),
   180	            "remaining_stack": remaining_stack,
   181	            "round_num": _non_negative_int(
   182	                recovery_metadata.get("round_num"), "round_num"
   183	            ),
   184	            "max_retries": 10,
   185	        },
   186	        "idempotency_key": f"recovery-cortex-scope-end:{failed_scope_id}",
   187	    }
   188	
   189	
   190	def _decode_json_dict(raw: Any) -> dict[str, Any]:
   191	    if isinstance(raw, dict):
   192	        return dict(raw)
   193	    if not raw:
   194	        return {}
   195	    try:
   196	        decoded = json.loads(raw)
   197	    except (json.JSONDecodeError, TypeError):
   198	        return {}
   199	    return decoded if isinstance(decoded, dict) else {}

## queue_service/session_outbox.py recovery/attach dispatch
   190	
   191	        return self.observed_handler.apply_wake_created(
   192	            effect=effect,
   193	            saga_id=saga_id,
   194	            scope_id=scope_id,
   195	            observed_at=self._clock(),
   196	        )
   197	
   198	    def _publish_recovery_archive(self, effect: dict[str, Any]) -> None:
   199	        payload = dict(effect.get("payload") or {})
   200	        scope_id = payload.get("scope_id")
   201	        if not scope_id:
   202	            raise ValueError("recovery archive outbox payload requires scope_id")
   203	        session_generation = require_positive_session_generation_value(
   204	            payload.get("session_generation"),
   205	            "recovery archive outbox payload",
   206	        )
   207	        remaining_stack = payload.get("remaining_stack")
   208	        if not isinstance(remaining_stack, dict):
   209	            raise ValueError(
   210	                "recovery archive outbox payload requires remaining_stack"
   211	            )
   212	        self.queue.publish(
   213	            TaskTopics.CORTEX_SCOPE_END,
   214	            {
   215	                "scope_id": scope_id,
   216	                "agent_root_scope_id": payload.get("agent_root_scope_id"),
   217	                "wake_scope_path": payload.get("wake_scope_path"),
   218	                "agent_id": payload.get("agent_id") or "",
   219	                "user_id": payload.get("user_id") or "",
   220	                "session_generation": session_generation,
   221	                "report": payload.get("report") or "",
   222	                "finalize_reason": payload.get("finalize_reason") or "recovery",
   223	                "remaining_stack": dict(remaining_stack),
   224	                "round_num": int(payload.get("round_num") or 0),
   225	            },
   226	            idempotency_key=effect.get("idempotency_key"),
   227	            max_retries=int(payload.get("max_retries") or 10),
   228	        )
   229	
   230	    def _publish_attach_input(self, effect: dict[str, Any]) -> dict[str, Any]:
   231	        payload = dict(effect.get("payload") or {})
   232	        message_ids = [
   233	            str(message_id)
   234	            for message_id in (payload.get("message_ids") or [])
   235	            if message_id
   236	        ]
   237	        if not message_ids:
   238	            raise ValueError("attach input outbox payload requires message_ids")
   239	        scope_id = str(payload.get("scope_id") or "")
   240	        if not scope_id:
   241	            raise ValueError("attach input outbox payload requires scope_id")
   242	        expected_generation = payload.get("expected_session_generation")
   243	        if expected_generation is None:
   244	            raise ValueError(
   245	                "attach input outbox payload requires expected_session_generation"
   246	            )
   247	        expected_generation = require_positive_session_generation_value(
   248	            expected_generation,
   249	            "attach input outbox payload",
   250	        )
   251	        agent_id = str(payload.get("agent_id") or "")
   252	        subagent_id = str(payload.get("subagent_id") or "")
   253	        if not agent_id or not subagent_id:
   254	            raise ValueError("attach input outbox payload requires agent_id/subagent_id")
   255	        task_id = self.queue.publish(
   256	            TaskTopics.SESSION_ATTACH_INPUT,
   257	            {
   258	                "agent_id": agent_id,
   259	                "subagent_id": subagent_id,
   260	                "user_id": str(payload.get("user_id") or ""),
   261	                "scope_id": scope_id,
   262	                "expected_wake_scope_id": scope_id,
   263	                "expected_session_generation": expected_generation,
   264	                "agent_root_scope_id": (
   265	                    payload.get("agent_root_scope_id")
   266	                    or derive_agent_root_scope_id(subagent_id)
   267	                ),
   268	                "trigger_type": str(payload.get("trigger_type") or ""),
   269	                "message_ids": message_ids,
   270	                "metadata": dict(payload.get("metadata") or {}),
   271	            },
   272	            idempotency_key=effect.get("idempotency_key"),
   273	            max_retries=int(payload.get("max_retries") or 10),
   274	        )
   275	        return {"task_id": task_id}

## queue_service/session_observed_events.py
     1	"""Observed event handlers for Queue session outbox publications."""
     2	
     3	from __future__ import annotations
     4	
     5	from typing import Any
     6	
     7	from queue_service.session_ledger import SessionLedgerRepository
     8	
     9	
    10	def _require_positive_generation(value: Any, owner: str) -> int:
    11	    if value is None:
    12	        raise ValueError(f"{owner} requires generation")
    13	    if isinstance(value, bool):
    14	        raise ValueError(f"{owner} requires positive generation")
    15	    try:
    16	        generation = int(value)
    17	    except (TypeError, ValueError) as exc:
    18	        raise ValueError(f"{owner} requires positive generation") from exc
    19	    if generation < 1:
    20	        raise ValueError(f"{owner} requires positive generation")
    21	    return generation
    22	
    23	
    24	class SessionObservedEventHandler:
    25	    """Apply observed side-effect results to the durable session ledger."""
    26	
    27	    def __init__(self, *, ledger: SessionLedgerRepository, saga_repository):
    28	        self.ledger = ledger
    29	        self.saga_repository = saga_repository
    30	
    31	    def apply_wake_created(
    32	        self,
    33	        *,
    34	        effect: dict[str, Any],
    35	        saga_id: str,
    36	        scope_id: str,
    37	        observed_at: str,
    38	    ) -> dict[str, Any]:
    39	        payload = dict(effect.get("payload") or {})
    40	        session_key = _required_payload_str(
    41	            payload,
    42	            "session_key",
    43	            "wake-created observation requires session_key",
    44	        )
    45	        agent_id = _required_payload_str(
    46	            payload,
    47	            "agent_id",
    48	            "wake-created observation requires agent_id",
    49	        )
    50	        subagent_id = _required_payload_str(
    51	            payload,
    52	            "subagent_id",
    53	            "wake-created observation requires subagent_id",
    54	        )
    55	
    56	        with self.ledger.db.transaction(lock_type="global"):
    57	            state = self.ledger.get_state(session_key)
    58	            generation = _require_positive_generation(
    59	                payload.get("generation"),
    60	                "wake-created observation",
    61	            )
    62	            state_is_active = (
    63	                state
    64	                and state.get("state") == "active"
    65	                and state.get("active_saga_id")
    66	                and state.get("active_scope_id")
    67	            )
    68	            winner_saga_id = saga_id
    69	            winner_scope_id = scope_id
    70	            if state_is_active:
    71	                winner_saga_id = str(state.get("active_saga_id") or "")
    72	                winner_scope_id = str(state.get("active_scope_id") or "")
    73	                if winner_saga_id != saga_id:
    74	                    self._cancel_pending_saga(
    75	                        saga_id=saga_id,
    76	                        observed_at=observed_at,
    77	                        reason="create_wake_saga outbox race loser",
    78	                    )
    79	                    return {
    80	                        "saga_id": winner_saga_id,
    81	                        "scope_id": winner_scope_id,
    82	                        "active_inserted": False,
    83	                        "race_lost": True,
    84	                    }
    85	            elif not self._matches_starting_state(
    86	                state=state,
    87	                scope_id=scope_id,
    88	                generation=generation,
    89	            ):
    90	                self._cancel_pending_saga(
    91	                    saga_id=saga_id,
    92	                    observed_at=observed_at,
    93	                    reason="stale create_wake_saga observation",
    94	                )
    95	                return {
    96	                    "saga_id": None,
    97	                    "scope_id": None,
    98	                    "active_inserted": False,
    99	                    "race_lost": True,
   100	                    "stale_observation": True,
   101	                }
   102	
   103	            self.ledger.record_active_session(
   104	                session_key=session_key,
   105	                generation=generation,
   106	                agent_id=agent_id,
   107	                subagent_id=subagent_id,
   108	                user_id=payload.get("user_id"),
   109	                active_saga_id=winner_saga_id,
   110	                active_scope_id=winner_scope_id,
   111	                updated_at=observed_at,
   112	            )
   113	
   114	            input_event_ids = [
   115	                str(event_id)
   116	                for event_id in (payload.get("input_event_ids") or [])
   117	                if event_id
   118	            ]
   119	            consume_reason = str(payload.get("consume_reason") or "")
   120	            if input_event_ids and consume_reason:
   121	                self.ledger.record_input_consumed(
   122	                    session_key=session_key,
   123	                    agent_id=agent_id,
   124	                    subagent_id=subagent_id,
   125	                    user_id=payload.get("user_id"),
   126	                    active_scope_id=winner_scope_id,
   127	                    event_ids=input_event_ids,
   128	                    reason=consume_reason,
   129	                    result={
   130	                        "action": payload.get("result_action") or "wake_saga_created",
   131	                        "saga_id": winner_saga_id,
   132	                        "scope_id": winner_scope_id,
   133	                    },
   134	                    consumed_at=observed_at,
   135	                )
   136	
   137	        return {
   138	            "saga_id": winner_saga_id,
   139	            "scope_id": winner_scope_id,
   140	            "active_inserted": not bool(state_is_active),
   141	            "race_lost": False,
   142	        }
   143	
   144	    @staticmethod
   145	    def _matches_starting_state(
   146	        *,
   147	        state: dict[str, Any] | None,
   148	        scope_id: str,
   149	        generation: int,
   150	    ) -> bool:
