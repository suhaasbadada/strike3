import { TreeNode, TreeEdge } from "./types";

export function calculateTreeLayout(nodes: TreeNode[], edges: TreeEdge[]) {
    if (!nodes || nodes.length === 0) return { nodes: [], edges: [], width: 240, height: 90 };

    const adj: Record<string, { childId: string, label: string }[]> = {};
    const inDegree: Record<string, number> = {};

    nodes.forEach(n => {
        adj[n.id.toString()] = [];
        inDegree[n.id.toString()] = 0;
    });

    edges.forEach(e => {
        const fromStr = e.from.toString();
        const toStr = e.to.toString();
        if (!adj[fromStr]) adj[fromStr] = [];
        adj[fromStr].push({ childId: toStr, label: e.label });
        inDegree[toStr] = (inDegree[toStr] || 0) + 1;
    });

    let rootId = nodes[0].id.toString();
    for (const n of nodes) {
        if (inDegree[n.id.toString()] === 0) {
            rootId = n.id.toString();
            break;
        }
    }

    let xIndex = 0;
    const X_SPACING = 30;
    const Y_SPACING = 45;
    const pos: Record<string, { x: number, y: number, depth: number }> = {};
    let maxDepth = 0;

    function traverse(nodeId: string, depth: number): { x: number, y: number } {
        if (depth > maxDepth) maxDepth = depth;

        const children = adj[nodeId] || [];
        const left = children.find(c => c.label === '0');
        const right = children.find(c => c.label === '1');

        let leftPos, rightPos;
        if (left) leftPos = traverse(left.childId, depth + 1);
        if (right) rightPos = traverse(right.childId, depth + 1);

        let x;
        if (leftPos && rightPos) {
            x = (leftPos.x + rightPos.x) / 2;
        } else if (leftPos) {
            x = leftPos.x + X_SPACING / 2;
        } else if (rightPos) {
            x = rightPos.x - X_SPACING / 2;
        } else {
            x = xIndex * X_SPACING;
            xIndex++;
        }

        pos[nodeId] = { x, y: depth * Y_SPACING, depth };
        return pos[nodeId];
    }

    if (nodes.find(n => n.id.toString() === rootId)) {
        traverse(rootId, 0);
    }

    const layoutNodes = nodes.map(n => ({
        ...n,
        x: pos[n.id.toString()]?.x || 0,
        y: (pos[n.id.toString()]?.y || 0) + 20,
        depth: pos[n.id.toString()]?.depth || 0
    }));

    const layoutEdges = edges.map(e => ({
        ...e,
        x1: pos[e.from.toString()]?.x || 0,
        y1: (pos[e.from.toString()]?.y || 0) + 20,
        x2: pos[e.to.toString()]?.x || 0,
        y2: (pos[e.to.toString()]?.y || 0) + 20
    }));

    const minX = Math.min(...layoutNodes.map(n => n.x));
    if (minX < 20) {
        const offsetX = Math.abs(minX) + 40;
        layoutNodes.forEach(n => n.x += offsetX);
        layoutEdges.forEach(e => {
            e.x1 += offsetX;
            e.x2 += offsetX;
        });
    }

    const maxX = Math.max(...layoutNodes.map(n => n.x));
    const minXPost = Math.min(...layoutNodes.map(n => n.x));

    return {
        nodes: layoutNodes,
        edges: layoutEdges,
        width: Math.max(240, maxX - minXPost + 80),
        height: Math.max(90, maxDepth * Y_SPACING + 60)
    };
}
