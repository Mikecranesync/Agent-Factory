"""
Slack Supervisor Demo - Complete usage examples
"""

import asyncio
import time
from agent_factory.observability import (
    agent_task,
    supervised_agent,
    SlackSupervisor,
    AgentCheckpoint,
    AgentStatus,
    SyncCheckpointEmitter
)


# Example 1: Basic Context Manager
async def example_basic():
    """Basic agent task with checkpoints."""
    print("\n=== Example 1: Basic Context Manager ===")

    async with agent_task(
        agent_id='demo-basic',
        task_name='Process 100 files',
        repo_scope='agent-factory'
    ) as ctx:
        await ctx.checkpoint('Reading files', progress=20)
        await asyncio.sleep(0.5)  # Simulate work

        await ctx.checkpoint('Processing files', progress=50)
        await asyncio.sleep(0.5)

        await ctx.checkpoint('Writing results', progress=80)
        await asyncio.sleep(0.5)

        ctx.add_artifact('output/results.json')
        ctx.update_tokens(50000)


# Example 2: Decorator Pattern
@supervised_agent(
    agent_id='demo-decorator',
    task_name='Refactor Auth Module',
    repo_scope='api-server'
)
async def example_decorator(ctx):
    """Agent function using decorator."""
    print("\n=== Example 2: Decorator Pattern ===")

    await ctx.checkpoint('Analyzing code', progress=30)
    await asyncio.sleep(0.5)

    await ctx.checkpoint('Applying changes', progress=70)
    await asyncio.sleep(0.5)

    ctx.add_artifact('https://github.com/user/repo/pull/123')
    return {'status': 'success', 'files_changed': 5}


# Example 3: Manual Supervisor
async def example_manual():
    """Manual supervisor usage."""
    print("\n=== Example 3: Manual Supervisor ===")

    supervisor = SlackSupervisor()

    # Post start
    thread_ts = await supervisor.post_task_start(
        agent_id='demo-manual',
        task_name='Deploy to Production',
        plan='1. Build\n2. Test\n3. Deploy',
        repo_scope='api-server'
    )

    await asyncio.sleep(0.5)

    # Post checkpoint
    cp = AgentCheckpoint(
        agent_id='demo-manual',
        task_name='Deploy to Production',
        status=AgentStatus.WORKING,
        progress=50,
        tokens_used=10000,
        last_action='Running integration tests',
        elapsed_seconds=30
    )
    await supervisor.post_checkpoint(cp, thread_ts=thread_ts, force=True)

    await asyncio.sleep(0.5)

    # Post complete
    await supervisor.post_task_complete(
        agent_id='demo-manual',
        task_name='Deploy to Production',
        summary='Deployment successful',
        artifacts=['https://app.example.com'],
        pr_url='https://github.com/user/repo/pull/456'
    )

    await supervisor.close()


# Example 4: Error Handling
async def example_error():
    """Agent with error handling."""
    print("\n=== Example 4: Error Handling ===")

    try:
        async with agent_task(
            agent_id='demo-error',
            task_name='Process Data',
            repo_scope='data-pipeline'
        ) as ctx:
            await ctx.checkpoint('Loading data', progress=20)
            await asyncio.sleep(0.5)

            await ctx.checkpoint('Validating data', progress=40)
            await asyncio.sleep(0.5)

            # Simulate error
            raise ValueError("Invalid data format in row 42")

    except ValueError as e:
        print(f"[ERROR] Caught: {e}")
        # Error is automatically posted to Slack by context manager


# Example 5: Token Usage Warning
async def example_token_warning():
    """Agent that triggers token usage warning."""
    print("\n=== Example 5: Token Usage Warning ===")

    async with agent_task(
        agent_id='demo-tokens',
        task_name='Generate Large Report',
        repo_scope='reports'
    ) as ctx:
        await ctx.checkpoint('Starting report generation', progress=10)
        ctx.update_tokens(50000)
        await asyncio.sleep(0.5)

        await ctx.checkpoint('Processing data', progress=50)
        ctx.update_tokens(140000)  # 70% warning
        await asyncio.sleep(0.5)

        await ctx.checkpoint('Finalizing report', progress=90)
        ctx.update_tokens(180000)  # 90% critical warning
        await asyncio.sleep(0.5)


# Example 6: Multi-Stage Pipeline
async def example_pipeline():
    """Multi-stage agent pipeline."""
    print("\n=== Example 6: Multi-Stage Pipeline ===")

    async with agent_task(
        agent_id='demo-pipeline',
        task_name='Full CI/CD Pipeline',
        repo_scope='web-app'
    ) as main_ctx:
        await main_ctx.checkpoint('Starting pipeline', progress=5)

        # Stage 1: Tests
        await main_ctx.checkpoint('Running tests (stage 1/4)', progress=25)
        await asyncio.sleep(0.5)
        main_ctx.add_artifact('test-results.xml')

        # Stage 2: Build
        await main_ctx.checkpoint('Building Docker image (stage 2/4)', progress=50)
        await asyncio.sleep(0.5)
        main_ctx.add_artifact('docker.io/org/app:v1.2.3')

        # Stage 3: Deploy Staging
        await main_ctx.checkpoint('Deploying to staging (stage 3/4)', progress=75)
        await asyncio.sleep(0.5)
        main_ctx.add_artifact('https://staging.example.com')

        # Stage 4: Deploy Production
        await main_ctx.checkpoint('Deploying to production (stage 4/4)', progress=95)
        await asyncio.sleep(0.5)
        main_ctx.add_artifact('https://app.example.com')

        await main_ctx.checkpoint('Pipeline complete', progress=100)


# Example 7: Sync Checkpoint Emitter (for subprocess agents)
def example_sync():
    """Synchronous checkpoint emitter for subprocess agents."""
    print("\n=== Example 7: Sync Checkpoint Emitter ===")

    emitter = SyncCheckpointEmitter(
        agent_id='demo-subprocess',
        task_name='Background Data Processing',
        repo_scope='data-warehouse'
    )

    emitter.emit('Starting background job', status='starting', progress=0)
    time.sleep(0.5)

    emitter.emit('Processing batch 1/10', status='working', progress=10)
    time.sleep(0.5)

    emitter.emit('Processing batch 5/10', status='working', progress=50)
    time.sleep(0.5)

    emitter.emit('Processing batch 10/10', status='working', progress=100)
    time.sleep(0.5)

    emitter.emit('Job complete', status='complete', progress=100)


# Example 8: Forced Checkpoints
async def example_forced():
    """Agent with forced immediate checkpoints."""
    print("\n=== Example 8: Forced Checkpoints ===")

    async with agent_task(
        agent_id='demo-forced',
        task_name='Critical System Update',
        repo_scope='infrastructure'
    ) as ctx:
        # Normal checkpoints (rate limited to 30s)
        await ctx.checkpoint('Reading config', progress=20)
        await ctx.checkpoint('Validating config', progress=40)

        # Force immediate post (ignore rate limit)
        await ctx.checkpoint('CRITICAL: Applying changes', progress=60, force=True)
        await asyncio.sleep(0.5)

        await ctx.checkpoint('CRITICAL: Restarting services', progress=80, force=True)
        await asyncio.sleep(0.5)

        await ctx.checkpoint('System update complete', progress=100, force=True)


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Slack Supervisor Demo")
    print("=" * 60)
    print("\nNote: Slack posting disabled in demo mode.")
    print("Set SLACK_BOT_TOKEN to enable real Slack updates.")
    print("")

    # Run examples
    await example_basic()
    await example_decorator()
    await example_manual()
    await example_error()
    await example_token_warning()
    await example_pipeline()
    example_sync()  # Synchronous
    await example_forced()

    print("\n" + "=" * 60)
    print("Demo Complete")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
