package com.forensic.controller;

// import com.forensic.entity.Node;
// import com.forensic.entity.Link;
import org.springframework.web.bind.annotation.*;

import com.forensic.dto.GraphDto;
import com.forensic.service.GraphService;
import lombok.RequiredArgsConstructor;

@RestController
@RequestMapping("/api/graph")
@RequiredArgsConstructor
public class GraphController {

    private final GraphService graphService;

    @GetMapping("/{caseId}")
    public GraphDto load(@PathVariable Long caseId) {
        return graphService.loadGraph(caseId);
    }

    @PostMapping("/")
    public GraphDto save(@RequestBody GraphDto graphDto) {
        return graphService.saveGraph(graphDto);
    }

    // @PostMapping("/nodes")
    // public Node addNode(
    //     @PathVariable Long caseId,
    //     @RequestBody Node node
    // ) {
    //     node.setCaseId(caseId);
    //     return graphService.addNode(node);
    // }

    // @PostMapping("/links")
    // public Link addLink(
    //     @PathVariable Long caseId,
    //     @RequestBody Link link
    // ) {
    //     link.setCaseId(caseId);
    //     return graphService.addLink(link);
    // }

    // @DeleteMapping("/nodes/{nodeId}")
    // public void deleteNode(
    //     @PathVariable Long caseId,
    //     @PathVariable Long nodeId
    // ) {
    //     graphService.deleteNode(caseId, nodeId);
    // }

    // @DeleteMapping("/links/{linkId}")
    // public void deleteLink(
    //     @PathVariable Long caseId,
    //     @PathVariable Long linkId
    // ) {
    //     graphService.deleteLink(caseId, linkId);
    // }
}
