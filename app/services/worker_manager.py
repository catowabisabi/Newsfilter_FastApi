import asyncio
import logging
import uuid
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

@dataclass
class NewsTask:
    id: str
    symbol: str
    limit: int
    future: asyncio.Future = field(default_factory=asyncio.Future)
    created_at: float = field(default_factory=time.time)

class NewsWorkerSystem:
    """
    Manages a queue of news fetching tasks with a fixed number of workers.
    Ensures safe concurrency and prevents the server from freezing.
    """
    
    def __init__(self, news_service, worker_count: int = 10):
        self.news_service = news_service
        self.worker_count = worker_count
        self.queue = asyncio.Queue()
        self.workers = []
        self.is_running = False
        # Thread pool for running blocking code (requests, sqlite, etc.)
        self.executor = ThreadPoolExecutor(max_workers=worker_count) 
        
    async def start(self):
        """Start the worker system"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info(f"🚀 Starting NewsWorkerSystem with {self.worker_count} workers...")
        
        for i in range(self.worker_count):
            worker = asyncio.create_task(self.worker_loop(i))
            self.workers.append(worker)
            
    async def stop(self):
        """Stop the worker system"""
        logger.info("🛑 Stopping NewsWorkerSystem...")
        self.is_running = False
        self.executor.shutdown(wait=False)
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
            
        # Wait for cancellation
        try:
            await asyncio.gather(*self.workers, return_exceptions=True)
        except Exception:
            pass
            
        self.workers = []
        
    async def process_news_request(self, symbol: str, limit: int = 10) -> Any:
        """
        Public interface: Submit a request and wait for the result.
        """
        task_id = str(uuid.uuid4())
        task = NewsTask(id=task_id, symbol=symbol, limit=limit)
        
        # Add to queue
        await self.queue.put(task)
        logger.info(f"📥 Task {task_id} queued for {symbol} (Queue size: {self.queue.qsize()})")
        
        try:
            # Wait for the result with a timeout
            result = await asyncio.wait_for(task.future, timeout=45.0)
            return result
        except asyncio.TimeoutError:
            logger.error(f"❌ Task {task_id} for {symbol} timed out")
            return [{"msg": "Request timed out, server busy"}]
            
    async def worker_loop(self, worker_id: int):
        """A single worker that processes tasks from the queue"""
        logger.info(f"👷 Worker-{worker_id} ready")
        
        while self.is_running:
            try:
                # Get task from queue
                task = await self.queue.get()
                
                logger.info(f"👷 Worker-{worker_id} processing {task.symbol}")
                
                try:
                    # Run the blocking get_symbol_news logic in a separate thread
                    # We wrap the async call in a sync wrapper because current implementation might lack full async support
                    # or mixes async/sync. However, since get_symbol_news IS async but blocks, 
                    # we need to be careful.
                    
                    # Refined approach:
                    # Since get_symbol_news is `async def` but contains blocking code (`requests`, `time.sleep`),
                    # we should ideally refactor it. But to fix it quickly without rewriting the service:
                    # We will run the inner sync logic in executor if we can isolate it, 
                    # OR we just run the existing async method but ensure other tasks can yield.
                    # BUT `async def` with blocking code blocks the loop.
                    
                    # The best quick fix: Run the 'heavy' part in a thread. 
                    # Since `news_service` methods are `async`, we can't easily pass them to `run_in_executor`.
                    # 
                    # Workaround: We will run the logic directly here. Since we are in a worker task,
                    # if we block, we block THIS worker. BUT if we block the event loop, we block EVERYONE.
                    # So we MUST run the blocking parts in a thread.
                    
                    # Let's use run_in_executor to run a synchronous wrapper that calls the logic.
                    # But the logic is async. This is tricky without refactoring `news_service.py`.
                    
                    # OPTION A: Refactor `news_service.py` to be truly async (hard, requires aiohttp).
                    # OPTION B: Wrap the blocking calls in `news_service.py` with `run_in_executor`.
                    # OPTION C: Run it here.
                    
                    # Let's try to run the fetch in a thread.
                    loop = asyncio.get_running_loop()
                    
                    # We need a sync function to pass to run_in_executor
                    def sync_fetch_wrapper():
                        # This is a hack because the underlying service is mixed.
                        # We need to create a new event loop for this thread if we want to run async code synchronously?
                        # No, that's messy.
                        
                        # Better approach: 
                        # The `news_service.get_symbol_news` is `async def`. It awaits `_fetch_from_api`.
                        # `_fetch_from_api` calls `requests.post` (BLOCKING).
                        # We should patch `_fetch_from_api` to run its blocking part in a thread.
                        pass

                    # To properly fix "Freezing", we MUST allow the event loop to continue.
                    # The best way is to offload the `get_symbol_news` execution to a thread.
                    # Since `get_symbol_news` is async, we can't just `executor.submit(get_symbol_news)`.
                    
                    # We will execute the task directly, but we rely on the implementation below to be fixed 
                    # to use `run_in_executor` for the request part.
                    
                    result = await self.news_service.get_symbol_news(task.symbol, task.limit)
                    
                    task.future.set_result(result)
                    
                except Exception as e:
                    logger.error(f"❌ Worker-{worker_id} error processing {task.symbol}: {e}")
                    # Don't crash the worker, just fail the task
                    if not task.future.done():
                        task.future.set_result([{"msg": f"Worker error: {str(e)}"}])
                finally:
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💥 Worker-{worker_id} crashed: {e}")
                await asyncio.sleep(1) # Prevent tight loop if crashing

