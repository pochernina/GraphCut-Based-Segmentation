from audioop import add
import numpy as np
from PIL import Image
import pymaxflow

def graphcut_segment(img, fg_pixels, bg_pixels):
    # parameters
    eps = 1e-9
    infty = 1e9
    alpha = 42
    sigma = 1.0 / 10.0


    def create_graph(vertices_count, edges_count):
        return pymaxflow.PyGraph(vertices_count, edges_count)
        
    def add_nodes(graph, count):
        graph.add_node(count)

    def add_edges(graph, src_vertices, dst_vertices, weights, reverse_weights):
        graph.add_edge_vectorized(src_vertices, dst_vertices, weights, reverse_weights)
    
    def set_foreground_weights(graph, points, indexes_array, weight=1e10):
        indexes = indexes_array[points[:, 1], points[:, 0]].ravel()
        graph.add_tweights_vectorized(indexes, np.zeros(len(points), np.float32),
                                      np.full(len(points), weight, dtype=np.float32))
    
    def set_background_weights(graph, points, indexes_array, weight=1e10):
        indexes = indexes_array[points[:, 1], points[:, 0]].ravel()
        graph.add_tweights_vectorized(indexes, np.full(len(points), weight, dtype=np.float32),
                                      np.zeros(len(points), np.float32))
    
    def add_term_edges(graph, indexes, weights_up, weights_down):
        graph.add_tweights_vectorized(indexes, weights_up, weights_down)

    def adj_dist(v1, v2):
        return np.exp(-sigma * np.abs(v1 - v2) / 2)
    
    def term_weights(im, fg_pixels, bg_pixels):
        fg_hist, fg_bins = np.histogram(im[fg_pixels[:, 1], fg_pixels[:, 0]],
                                        bins=8, range=(0, 256), density=True)
        bg_hist, bg_bins = np.histogram(im[bg_pixels[:, 1], bg_pixels[:, 0]],
                                        bins=8, range=(0, 256), density=True)

        fg_ind = np.searchsorted(fg_bins[1:-1], im.flatten())
        bg_ind = np.searchsorted(bg_bins[1:-1], im.flatten())

        fg_prob = fg_hist[fg_ind] + eps
        bg_prob = bg_hist[bg_ind] + eps

        fg_weights = -np.log(fg_prob)
        bg_weights = -np.log(bg_prob)
        return fg_weights, bg_weights


    # a color image to greyscale then to array
    im = np.array(img.convert('L')) 

    indexes = np.arange(im.size, dtype=np.int32).reshape(im.shape)
    fg_pixels = np.array(fg_pixels, dtype=int) 
    bg_pixels = np.array(bg_pixels, dtype=int)

    graph = create_graph(im.size, im.size * 4)
    add_nodes(graph, im.size)

    # adjacent right
    weights = (adj_dist(im[:, 1:], im[:, :-1])).astype(np.float32).ravel()
    e1 = indexes[:, :-1].ravel()
    e2 = indexes[:, 1:].ravel()
    add_edges(graph, e1, e2, alpha * weights, 0 * weights)

    # adjacent left
    weights = (adj_dist(im[:, :-1], im[:, 1:])).astype(np.float32).ravel()
    e1 = indexes[:, 1:].ravel()
    e2 = indexes[:, :-1].ravel()
    add_edges(graph, e1, e2, 0 * weights, alpha * weights)

    # adjacent down
    weights = (adj_dist(im[1:, :], im[:-1, :])).astype(np.float32).ravel()
    e1 = indexes[:-1, :].ravel()
    e2 = indexes[1:, :].ravel()
    add_edges(graph, e1, e2, alpha * weights, 0 * weights)

    # adjacent up
    weights = (adj_dist(im[:-1, :], im[1:, :])).astype(np.float32).ravel()
    e1 = indexes[1:, :].ravel()
    e2 = indexes[:-1, :].ravel()
    add_edges(graph, e1, e2, 0 * weights, alpha * weights)
    
    '''
    # adjacent right and down
    weights = (adj_dist(im[1:, 1:], im[:-1, :-1])).astype(np.float32).ravel()
    e1 = indexes[:-1, :-1].ravel()
    e2 = indexes[1:, 1:].ravel()
    add_edges(graph, e1, e2, alpha * weights, 0 * weights)

    # adjacent left and up
    weights = (adj_dist(im[:-1, :-1], im[1:, 1:])).astype(np.float32).ravel()
    e1 = indexes[1:, 1:].ravel()
    e2 = indexes[:-1, :-1].ravel()
    add_edges(graph, e1, e2, 0 * weights, alpha * weights)

    # adjacent right and up
    weights = (adj_dist(im[1:, :-1], im[:-1, 1:])).astype(np.float32).ravel()
    e1 = indexes[:-1, 1:].ravel()
    e2 = indexes[1:, :-1].ravel()
    add_edges(graph, e1, e2, alpha * weights, 0 * weights)

    # adjacent left and down
    weights = (adj_dist(im[:-1, 1:], im[1:, :-1])).astype(np.float32).ravel()
    e1 = indexes[1:, :-1].ravel()
    e2 = indexes[:-1, 1:].ravel()
    add_edges(graph, e1, e2, 0 * weights, alpha * weights)
    '''
    
    fg_weights, bg_weights = term_weights(im, fg_pixels, bg_pixels)
    add_term_edges(graph, indexes.ravel(), fg_weights.astype(np.float32).ravel(),
                                           bg_weights.astype(np.float32).ravel())

    # links the to source and sink
    set_foreground_weights(graph, fg_pixels, indexes, infty)
    set_background_weights(graph, bg_pixels, indexes, infty)

    graph.maxflow()

    mask = graph.what_segment_vectorized()
    # 0 for background, 1 for object
    return mask.reshape(im.shape)

def predict(img, fg_pixels, bg_pixels):
    mask = graphcut_segment(img, fg_pixels, bg_pixels)

    mask_a = img.copy()
    mask_a = np.asarray(mask_a).astype('uint8')
    mask_a[mask==0] = (0, 0, 255)
    mask_a[mask==1] = (255, 0, 0)
    mask_a = Image.fromarray(mask_a.astype('uint8'), 'RGB')
    mask_a.putalpha(130)

    img_a = img.copy()
    img_a.putalpha(255)

    im = Image.alpha_composite(img_a, mask_a)
    # im.save("result3.png", "PNG")

    return im